"""Traffic service - Yandex Traffic tiles parsing + TomTom fallback."""
import asyncio
import logging
import math
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from io import BytesIO
from collections import Counter

import aiohttp

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    logging.warning("Pillow not installed, Yandex traffic parsing disabled")

from bot.config import settings

logger = logging.getLogger(__name__)

# Moscow timezone
MOSCOW_TZ = ZoneInfo("Europe/Moscow")


def get_moscow_time() -> datetime:
    """Get current time in Moscow timezone."""
    return datetime.now(MOSCOW_TZ)


class TrafficData:
    """Traffic data for a region."""
    def __init__(self, region: str, level: int, description: str, timestamp: datetime):
        self.region = region
        self.level = level  # 1-10 scale
        self.description = description
        self.timestamp = timestamp

    @property
    def emoji(self) -> str:
        """Get emoji based on traffic level."""
        if self.level <= 3:
            return "🟢"
        elif self.level <= 6:
            return "🟡"
        elif self.level <= 8:
            return "🟠"
        else:
            return "🔴"

    @property
    def status_text(self) -> str:
        """Get human-readable status."""
        if self.level <= 3:
            return "Свободно"
        elif self.level <= 6:
            return "Средние пробки"
        elif self.level <= 8:
            return "Затруднено"
        else:
            return "Серьезные пробки"


# Cache for traffic data
_traffic_cache: dict[str, TrafficData] = {}
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 180  # 3 minutes - optimal balance between freshness and safety


def clear_traffic_cache():
    """Clear traffic cache to force refresh."""
    global _traffic_cache, _cache_timestamp
    _traffic_cache.clear()
    _cache_timestamp = None
    logger.info("Traffic cache cleared")


async def _download_yandex_traffic_map(lat: float, lon: float, zoom: int = 13) -> Optional[bytes]:
    """
    Download Yandex static map with traffic layer for given coordinates.

    Uses Yandex Static Maps API which is more reliable than tiles.

    Args:
        lat: Latitude
        lon: Longitude
        zoom: Zoom level (13 is good for city areas)

    Returns:
        PNG image bytes or None if failed
    """
    if not PILLOW_AVAILABLE:
        return None

    # Yandex Static Maps API
    url = 'https://static-maps.yandex.ru/1.x/'
    params = {
        'l': 'map,trf',  # map + traffic layer
        'll': f'{lon},{lat}',  # lon,lat format
        'z': str(zoom),
        'size': '450,450',
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
                    logger.debug(f"Failed to download Yandex map: {resp.status}")
                    return None
    except Exception as e:
        logger.debug(f"Error downloading Yandex map: {e}")
        return None


def _analyze_traffic_colors(image_data: bytes) -> int:
    """
    Analyze Yandex traffic tile colors to estimate traffic level.

    Yandex traffic colors:
    - Green: Free flow (1-3)
    - Yellow: Medium traffic (4-6)
    - Orange: Heavy traffic (7-8)
    - Red: Jammed (9-10)

    Returns:
        Traffic level 1-10
    """
    if not PILLOW_AVAILABLE:
        return 5

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
            # No traffic data in tile, return medium
            return 5

        # Calculate weighted traffic level
        red_ratio = red_pixels / total_traffic
        orange_ratio = orange_pixels / total_traffic
        yellow_ratio = yellow_pixels / total_traffic
        green_ratio = green_pixels / total_traffic

        # Weight: red=10, orange=8, yellow=5, green=2
        # Adjusted weights to better reflect Moscow traffic conditions
        traffic_level = (
            red_ratio * 10 +
            orange_ratio * 8 +
            yellow_ratio * 5 +
            green_ratio * 2
        )

        # Ensure level is between 1-10
        return int(min(10, max(1, traffic_level)))

    except Exception as e:
        logger.debug(f"Error analyzing traffic colors: {e}")
        return 5


def _get_simulated_traffic_level() -> int:
    """
    Generate realistic traffic level based on time of day.

    Returns:
        Traffic level 1-10
    """
    hour = get_moscow_time().hour

    # Morning rush (7-10): high traffic
    if 7 <= hour < 10:
        return 7 + (hour - 7)  # 7, 8, 9
    # Midday (10-17): medium traffic
    elif 10 <= hour < 17:
        return 4 + ((hour - 10) % 3)  # 4-6
    # Evening rush (17-20): very high traffic
    elif 17 <= hour < 20:
        return 8 + (hour - 17) // 2  # 8-9
    # Night (20-7): low traffic
    else:
        return 2 + (hour % 2)  # 2-3


async def get_moscow_traffic() -> Optional[TrafficData]:
    """
    Get current traffic level for Moscow.

    Priority:
    1. Yandex traffic tiles parsing (if Pillow available)
    2. TomTom Traffic API (fallback)
    3. Simulated data (last resort)

    Returns:
        TrafficData object or None if failed
    """
    global _traffic_cache, _cache_timestamp

    # Check cache
    if _cache_timestamp and (get_moscow_time() - _cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
        return _traffic_cache.get("moscow")

    # Try Yandex traffic tiles parsing first
    if PILLOW_AVAILABLE:
        try:
            # Sample multiple points across Moscow for better accuracy
            moscow_points = [
                (55.7558, 37.6173),  # Center
                (55.7558, 37.5173),  # West
                (55.7558, 37.7173),  # East
                (55.8058, 37.6173),  # North
            ]

            traffic_levels = []

            for lat, lon in moscow_points:
                try:
                    image_data = await _download_yandex_traffic_map(lat, lon, zoom=13)
                    if image_data:
                        level = _analyze_traffic_colors(image_data)
                        traffic_levels.append(level)
                        logger.debug(f"Yandex map ({lat}, {lon}): level={level}")

                    # Small delay to be nice to Yandex servers
                    await asyncio.sleep(0.3)
                except Exception as e:
                    logger.debug(f"Failed to parse Yandex map ({lat}, {lon}): {e}")
                    continue

            if traffic_levels:
                # Average traffic level across all points
                avg_traffic_level = int(sum(traffic_levels) / len(traffic_levels))

                traffic_data = TrafficData(
                    region="moscow",
                    level=avg_traffic_level,
                    description=f"Пробки {avg_traffic_level} баллов",
                    timestamp=get_moscow_time()
                )

                # Update cache
                _traffic_cache["moscow"] = traffic_data
                _cache_timestamp = get_moscow_time()

                logger.info(f"Got traffic from Yandex tiles (avg of {len(traffic_levels)} points): level={avg_traffic_level}")
                return traffic_data
            else:
                logger.warning("Yandex tiles parsing failed, falling back to TomTom")

        except Exception as e:
            logger.warning(f"Yandex tiles parsing error: {e}, falling back to TomTom")

    # Fallback to TomTom Traffic API
    if settings.tomtom_api_key:
        try:
            # Multiple points across Moscow for better coverage
            # Reduced to 4 strategic points to save API calls while maintaining accuracy
            moscow_points = [
                (55.7558, 37.6173),  # Center (Kremlin area)
                (55.7558, 37.5173),  # West
                (55.7558, 37.7173),  # East
                (55.8058, 37.6173),  # North (MKAD area)
            ]

            traffic_levels = []

            # Disable SSL verification to avoid certificate issues on Windows
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                for lat, lon in moscow_points:
                    try:
                        url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

                        params = {
                            "key": settings.tomtom_api_key,
                            "point": f"{lat},{lon}",
                        }

                        headers = {
                            "User-Agent": "TaxiBot/1.0",
                        }

                        async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                            if resp.status == 200:
                                data = await resp.json()

                                flow_data = data.get("flowSegmentData", {})
                                current_speed = flow_data.get("currentSpeed", 50)
                                free_flow_speed = flow_data.get("freeFlowSpeed", 60)

                                if free_flow_speed > 0:
                                    speed_ratio = current_speed / free_flow_speed

                                    # More realistic traffic level calculation
                                    # 90-100% speed = 1-2 (free)
                                    # 70-90% speed = 3-4 (light)
                                    # 50-70% speed = 5-6 (medium)
                                    # 30-50% speed = 7-8 (heavy)
                                    # 0-30% speed = 9-10 (jammed)
                                    if speed_ratio >= 0.9:
                                        traffic_level = 1
                                    elif speed_ratio >= 0.7:
                                        traffic_level = int(3 + (0.9 - speed_ratio) * 10)
                                    elif speed_ratio >= 0.5:
                                        traffic_level = int(5 + (0.7 - speed_ratio) * 10)
                                    elif speed_ratio >= 0.3:
                                        traffic_level = int(7 + (0.5 - speed_ratio) * 10)
                                    else:
                                        traffic_level = min(10, int(9 + (0.3 - speed_ratio) * 10))

                                    traffic_level = max(1, min(10, traffic_level))
                                    traffic_levels.append(traffic_level)

                                    logger.debug("Point (%s, %s): speed=%d/%d (%.1f%%) -> level=%d",
                                               lat, lon, current_speed, free_flow_speed,
                                               speed_ratio * 100, traffic_level)
                    except Exception as e:
                        logger.debug("Failed to get traffic for point (%s, %s): %s", lat, lon, e)
                        continue

            if traffic_levels:
                # Average traffic level across all points
                avg_traffic_level = int(sum(traffic_levels) / len(traffic_levels))

                traffic_data = TrafficData(
                    region="moscow",
                    level=avg_traffic_level,
                    description=f"Пробки {avg_traffic_level} баллов",
                    timestamp=get_moscow_time()
                )

                # Update cache
                _traffic_cache["moscow"] = traffic_data
                _cache_timestamp = get_moscow_time()

                logger.info("Got real traffic data from TomTom (avg of %d points): level=%d",
                           len(traffic_levels), avg_traffic_level)
                return traffic_data
            else:
                logger.warning("TomTom API: no valid data points, falling back to simulation")

        except Exception as e:
            logger.warning("TomTom API failed: %s, falling back to simulation", e)

    # Fallback to simulated data
    traffic_level = _get_simulated_traffic_level()

    traffic_data = TrafficData(
        region="moscow",
        level=traffic_level,
        description=f"Пробки {traffic_level} баллов (симуляция)",
        timestamp=get_moscow_time()
    )

    # Update cache
    _traffic_cache["moscow"] = traffic_data
    _cache_timestamp = get_moscow_time()

    return traffic_data


async def get_mkad_traffic() -> Optional[TrafficData]:
    """Get traffic level for MKAD (Moscow Ring Road)."""
    # Simplified implementation - in reality would query specific MKAD data
    moscow_traffic = await get_moscow_traffic()

    if not moscow_traffic:
        return None

    # MKAD typically has higher traffic than average
    mkad_level = min(10, moscow_traffic.level + 1)

    return TrafficData(
        region="mkad",
        level=mkad_level,
        description=f"МКАД: {mkad_level} баллов",
        timestamp=get_moscow_time()
    )


async def get_ttk_traffic() -> Optional[TrafficData]:
    """Get traffic level for TTK (Third Transport Ring)."""
    # Simplified implementation
    moscow_traffic = await get_moscow_traffic()

    if not moscow_traffic:
        return None

    # TTK typically has similar or slightly higher traffic
    ttk_level = min(10, moscow_traffic.level + 1)

    return TrafficData(
        region="ttk",
        level=ttk_level,
        description=f"ТТК: {ttk_level} баллов",
        timestamp=get_moscow_time()
    )


def get_cached_traffic() -> dict[str, TrafficData]:
    """Get all cached traffic data."""
    return _traffic_cache.copy()


def get_traffic_recommendation(traffic_level: int, coefficient: float) -> str:
    """
    Get recommendation based on traffic and coefficient.

    Args:
        traffic_level: Traffic level (1-10)
        coefficient: Surge coefficient

    Returns:
        Recommendation text with emoji
    """
    if coefficient >= 2.0 and traffic_level <= 5:
        return "✅ Отличное время! Высокий кэф и нормальные дороги"
    elif coefficient >= 2.0 and traffic_level > 5:
        return "⚠️ Высокий кэф, но пробки. Будьте готовы к задержкам"
    elif coefficient < 1.5 and traffic_level > 7:
        return "❌ Низкий кэф и пробки. Не рекомендуется"
    elif traffic_level <= 3:
        return "🟢 Дороги свободны, хорошее время для работы"
    else:
        return "🟡 Средние условия"


class TrafficForecast:
    """Traffic forecast for the next hour."""
    def __init__(self, current_level: int, forecast_level: int, trend: str, confidence: str):
        self.current_level = current_level
        self.forecast_level = forecast_level
        self.trend = trend  # "increasing", "decreasing", "stable"
        self.confidence = confidence  # "high", "medium", "low"

    @property
    def trend_emoji(self) -> str:
        """Get emoji for trend."""
        if self.trend == "increasing":
            return "📈"
        elif self.trend == "decreasing":
            return "📉"
        else:
            return "➡️"

    @property
    def trend_text(self) -> str:
        """Get human-readable trend."""
        if self.trend == "increasing":
            return "Ухудшение"
        elif self.trend == "decreasing":
            return "Улучшение"
        else:
            return "Стабильно"


def _predict_traffic_change(current_hour: int, current_level: int) -> tuple[int, str, str, str]:
    """
    Predict traffic change for the next hour.

    Returns also a short explanation (basis) for diagnostics/UI.

    Args:
        current_hour: Current hour (0-23)
        current_level: Current traffic level (1-10)

    Returns:
        Tuple of (forecast_level, trend, confidence, basis)
    """
    next_hour = (current_hour + 1) % 24

    # Morning build-up (6-9)
    if 6 <= current_hour < 9:
        forecast_level = min(10, current_level + 2)
        trend = "increasing"
        confidence = "high"
        basis = "утренний разгон час-пика"
    # Morning peak turning (9-10)
    elif 9 <= current_hour < 10:
        forecast_level = max(1, current_level - 1)
        trend = "decreasing"
        confidence = "high"
        basis = "после пика утреннего час-пика"
    # Midday relatively stable (10-16)
    elif 10 <= current_hour < 16:
        forecast_level = current_level
        trend = "stable"
        confidence = "medium"
        basis = "дневная стабильная фаза"
    # Evening build-up (16-19)
    elif 16 <= current_hour < 19:
        forecast_level = min(10, current_level + 2)
        trend = "increasing"
        confidence = "high"
        basis = "вечерний разгон час-пика"
    # Evening decline (19-21)
    elif 19 <= current_hour < 21:
        forecast_level = max(1, current_level - 2)
        trend = "decreasing"
        confidence = "high"
        basis = "спад после вечернего пика"
    # Night tends to be low/stable (21-6)
    else:
        forecast_level = max(1, min(3, current_level))
        trend = "decreasing" if current_level > 3 else "stable"
        confidence = "medium"
        basis = "ночной период"

    return forecast_level, trend, confidence, basis


async def get_traffic_forecast(region: str = "moscow") -> Optional[TrafficForecast]:
    """Get traffic forecast for the next hour.

    Основание прогноза:
    - Берём текущее измеренное значение пробок (Яндекс тайлы / TomTom / симуляция)
    - Применяем простую эвристику по времени суток (час-пики)

    Args:
        region: "moscow", "mkad", "ttk"
    """
    # Get current traffic
    if region == "moscow":
        current_traffic = await get_moscow_traffic()
    elif region == "mkad":
        current_traffic = await get_mkad_traffic()
    elif region == "ttk":
        current_traffic = await get_ttk_traffic()
    else:
        return None

    if not current_traffic:
        return None

    # Predict change
    current_hour = get_moscow_time().hour
    forecast_level, trend, confidence, basis = _predict_traffic_change(current_hour, current_traffic.level)

    logger.info(
        "Traffic forecast: region=%s hour=%d current=%d -> forecast=%d trend=%s confidence=%s basis=%s",
        region,
        current_hour,
        current_traffic.level,
        forecast_level,
        trend,
        confidence,
        basis,
    )

    # Attach basis for UI if needed (monkey-patch attribute)
    try:
        forecast_obj = TrafficForecast(
            current_level=current_traffic.level,
            forecast_level=forecast_level,
            trend=trend,
            confidence=confidence,
        )
        forecast_obj.basis = basis  # type: ignore[attr-defined]
        return forecast_obj
    except Exception:
        return TrafficForecast(
            current_level=current_traffic.level,
            forecast_level=forecast_level,
            trend=trend,
            confidence=confidence,
        )

