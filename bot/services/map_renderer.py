import io
import logging
import math

from staticmap import StaticMap
from PIL import Image, ImageDraw

from bot.services.yandex_api import SurgeData
from bot.services.hex_grid import generate_hex_grid, _purple_hex_color, _purple_alpha

logger = logging.getLogger(__name__)

MAP_WIDTH = 800
MAP_HEIGHT = 600
# Moscow center and zoom for Mercator projection
CENTER_LAT = 55.7558
CENTER_LON = 37.6173
ZOOM = 10


def _latlon_to_pixel(lat: float, lon: float, center_lat: float, center_lon: float,
                     zoom: int, width: int, height: int) -> tuple[int, int]:
    """Convert lat/lon to pixel coordinates using Web Mercator."""
    n = 2.0 ** zoom * 256
    # Center pixel
    cx = n * (center_lon + 180) / 360
    cy = n * (1 - math.log(math.tan(math.radians(center_lat)) +
              1 / math.cos(math.radians(center_lat))) / math.pi) / 2
    # Target pixel
    px = n * (lon + 180) / 360
    py = n * (1 - math.log(math.tan(math.radians(lat)) +
              1 / math.cos(math.radians(lat))) / math.pi) / 2
    x = int(px - cx + width / 2)
    y = int(py - cy + height / 2)
    return x, y


def render_surge_map(data: list[SurgeData]) -> bytes | None:
    """Render a static map image with hexagonal surge zones. Returns PNG bytes."""
    if not data:
        return None

    # Get base map tiles
    m = StaticMap(MAP_WIDTH, MAP_HEIGHT,
                  url_template="https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    # Add a dummy marker at center so staticmap renders the right area
    from staticmap import CircleMarker
    m.add_marker(CircleMarker((CENTER_LON, CENTER_LAT), "#00000000", 1))

    try:
        base_image = m.render(zoom=ZOOM)
    except Exception as e:
        logger.error("Base map render error: %s", e)
        return None

    # Build tariff -> max coeff per zone for hex_grid
    # generate_hex_grid uses cached coefficients directly
    tariffs_in_data = set(sd.tariff for sd in data)
    tariff = list(tariffs_in_data)[0] if len(tariffs_in_data) == 1 else None
    cells = generate_hex_grid(tariff=tariff)

    if not cells:
        # Fallback: return base map
        buf = io.BytesIO()
        base_image.save(buf, format="PNG")
        return buf.getvalue()

    # Draw hexagons on overlay
    overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for cell in cells:
        pixels = []
        for v in cell.vertices:
            px, py = _latlon_to_pixel(v[0], v[1], CENTER_LAT, CENTER_LON,
                                      ZOOM, MAP_WIDTH, MAP_HEIGHT)
            pixels.append((px, py))

        color_hex = _purple_hex_color(cell.coefficient)
        alpha = _purple_alpha(cell.coefficient)
        # Parse hex color
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)
        # Almost transparent white outline for subtle separation
        draw.polygon(pixels, fill=(r, g, b, alpha), outline=(255, 255, 255, 15))

    # Composite
    result = Image.alpha_composite(base_image.convert("RGBA"), overlay)
    buf = io.BytesIO()
    result.save(buf, format="PNG")
    return buf.getvalue()
