"""Traffic service - Yandex Traffic API integration."""
import logging
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

import aiohttp

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
CACHE_TTL_SECONDS = 300  # 5 minutes


def clear_traffic_cache():
    """Clear traffic cache to force refresh."""
    global _traffic_cache, _cache_timestamp
    _traffic_cache.clear()
    _cache_timestamp = None
    logger.info("Traffic cache cleared")


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
    Get current traffic level for Moscow using TomTom API with multiple points.

    Returns:
        TrafficData object or None if failed
    """
    global _traffic_cache, _cache_timestamp

    # Check cache
    if _cache_timestamp and (get_moscow_time() - _cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
        return _traffic_cache.get("moscow")

    # Try TomTom Traffic API with multiple points across Moscow
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


def _predict_traffic_change(current_hour: int, current_level: int) -> tuple[int, str, str]:
    """
    Predict traffic change for the next hour.

    Args:
        current_hour: Current hour (0-23)
        current_level: Current traffic level (1-10)

    Returns:
        Tuple of (forecast_level, trend, confidence)
    """
    next_hour = (current_hour + 1) % 24

    # Morning rush building up (6-9)
    if 6 <= current_hour < 9:
        forecast_level = min(10, current_level + 2)
        trend = "increasing"
        confidence = "high"
    # Morning rush peak (9-10)
    elif 9 <= current_hour < 10:
        forecast_level = max(1, current_level - 1)
        trend = "decreasing"
        confidence = "high"
    # Midday stable (10-16)
    elif 10 <= current_hour < 16:
        forecast_level = current_level
        trend = "stable"
        confidence = "medium"
    # Evening rush building up (16-19)
    elif 16 <= current_hour < 19:
        forecast_level = min(10, current_level + 2)
        trend = "increasing"
        confidence = "high"
    # Evening rush declining (19-21)
    elif 19 <= current_hour < 21:
        forecast_level = max(1, current_level - 2)
        trend = "decreasing"
        confidence = "high"
    # Night stable (21-6)
    else:
        forecast_level = max(1, min(3, current_level))
        trend = "decreasing" if current_level > 3 else "stable"
        confidence = "medium"

    return forecast_level, trend, confidence


async def get_traffic_forecast(region: str = "moscow") -> Optional[TrafficForecast]:
    """
    Get traffic forecast for the next hour.

    Args:
        region: Region name ("moscow", "mkad", "ttk")

    Returns:
        TrafficForecast object or None if failed
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
    forecast_level, trend, confidence = _predict_traffic_change(current_hour, current_traffic.level)

    return TrafficForecast(
        current_level=current_traffic.level,
        forecast_level=forecast_level,
        trend=trend,
        confidence=confidence
    )
