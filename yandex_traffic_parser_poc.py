"""
PROOF OF CONCEPT: Parse Yandex traffic tiles to infer traffic level.

⚠️ WARNING: This is NOT recommended for production use!

Risks:
1. Violates Yandex Terms of Service
2. Can break at any time (endpoint changes)
3. Risk of IP blocking
4. Computationally expensive (image processing)
5. Less accurate than proper API
6. Legal/ethical concerns

This is for educational/research purposes only.
"""
import asyncio
import aiohttp
from PIL import Image
from io import BytesIO
from collections import Counter
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def latlon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to tile coordinates."""
    import math

    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)

    return x, y


async def download_traffic_tile(lat: float, lon: float, zoom: int = 12) -> Optional[bytes]:
    """
    Download Yandex traffic tile for given coordinates.

    Args:
        lat: Latitude
        lon: Longitude
        zoom: Zoom level (10-15 recommended)

    Returns:
        PNG image bytes or None if failed
    """
    x, y = latlon_to_tile(lat, lon, zoom)

    url = 'https://core-renderer-tiles.maps.yandex.net/tiles'
    params = {
        'l': 'trf',  # traffic layer
        'x': str(x),
        'y': str(y),
        'z': str(zoom),
        'scale': '1',
        'lang': 'ru_RU'
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://yandex.ru/maps/',
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.read()
                else:
                    logger.warning(f"Failed to download tile: {resp.status}")
                    return None
    except Exception as e:
        logger.error(f"Error downloading tile: {e}")
        return None


def analyze_traffic_colors(image_data: bytes) -> int:
    """
    Analyze traffic tile colors to estimate traffic level.

    Yandex traffic colors (approximate):
    - Green: Free flow
    - Yellow: Medium traffic
    - Orange: Heavy traffic
    - Red: Jammed

    Returns:
        Traffic level 1-10
    """
    try:
        img = Image.open(BytesIO(image_data))

        # Convert to RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')

        pixels = list(img.getdata())

        # Count traffic colors
        green_pixels = 0
        yellow_pixels = 0
        orange_pixels = 0
        red_pixels = 0

        for r, g, b in pixels:
            # Green: high green, low red/blue
            if g > 150 and r < 100 and b < 100:
                green_pixels += 1
            # Yellow: high red+green, low blue
            elif r > 150 and g > 150 and b < 100:
                yellow_pixels += 1
            # Orange: high red, medium green, low blue
            elif r > 200 and 80 < g < 180 and b < 80:
                orange_pixels += 1
            # Red: high red, low green/blue
            elif r > 180 and g < 100 and b < 100:
                red_pixels += 1

        total_traffic = green_pixels + yellow_pixels + orange_pixels + red_pixels

        if total_traffic == 0:
            # No traffic data in tile
            return 5  # Default medium

        # Calculate weighted traffic level
        red_ratio = red_pixels / total_traffic
        orange_ratio = orange_pixels / total_traffic
        yellow_ratio = yellow_pixels / total_traffic
        green_ratio = green_pixels / total_traffic

        # Weight: red=10, orange=7, yellow=4, green=1
        traffic_level = (
            red_ratio * 10 +
            orange_ratio * 7 +
            yellow_ratio * 4 +
            green_ratio * 1
        )

        return int(min(10, max(1, traffic_level)))

    except Exception as e:
        logger.error(f"Error analyzing traffic colors: {e}")
        return 5  # Default


async def get_yandex_traffic_level(lat: float, lon: float) -> int:
    """
    Get traffic level for coordinates by parsing Yandex tiles.

    ⚠️ NOT RECOMMENDED FOR PRODUCTION!

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Traffic level 1-10
    """
    image_data = await download_traffic_tile(lat, lon, zoom=12)

    if not image_data:
        return 5  # Default if failed

    return analyze_traffic_colors(image_data)


async def test_moscow_traffic():
    """Test traffic parsing for Moscow locations."""

    moscow_points = [
        (55.7558, 37.6173, "Center"),
        (55.7522, 37.6156, "Kremlin"),
        (55.7558, 37.5173, "West"),
        (55.7558, 37.7173, "East"),
        (55.8058, 37.6173, "North"),
        (55.7058, 37.6173, "South"),
    ]

    print("Testing Yandex traffic tile parsing...\n")

    for lat, lon, name in moscow_points:
        level = await get_yandex_traffic_level(lat, lon)
        print(f"{name:10} ({lat:.4f}, {lon:.4f}): Traffic level {level}/10")

        # Be nice to Yandex servers
        await asyncio.sleep(1)


if __name__ == "__main__":
    # Install required: pip install Pillow aiohttp
    asyncio.run(test_moscow_traffic())
