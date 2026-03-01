"""Traffic service - Yandex Traffic API integration."""
import logging
from typing import Optional
from datetime import datetime

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)


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


def _get_simulated_traffic_level() -> int:
    """
    Generate realistic traffic level based on time of day.

    Returns:
        Traffic level 1-10
    """
    hour = datetime.now().hour

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
    Get current traffic level for Moscow using TomTom API.

    Returns:
        TrafficData object or None if failed
    """
    global _traffic_cache, _cache_timestamp

    # Check cache
    if _cache_timestamp and (datetime.now() - _cache_timestamp).total_seconds() < CACHE_TTL_SECONDS:
        return _traffic_cache.get("moscow")

    # Try TomTom Traffic API
    if settings.tomtom_api_key:
        try:
            # TomTom Traffic Flow API
            # Moscow center coordinates
            lat, lon = 55.7558, 37.6173

            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

            params = {
                "key": settings.tomtom_api_key,
                "point": f"{lat},{lon}",
            }

            headers = {
                "User-Agent": "TaxiBot/1.0",
            }

            # Disable SSL verification to avoid certificate issues on Windows
            import ssl
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            connector = aiohttp.TCPConnector(ssl=ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Parse traffic data
                        # TomTom returns currentSpeed and freeFlowSpeed
                        flow_data = data.get("flowSegmentData", {})
                        current_speed = flow_data.get("currentSpeed", 50)
                        free_flow_speed = flow_data.get("freeFlowSpeed", 60)

                        # Calculate traffic level (1-10) based on speed ratio
                        # 100% speed = level 1 (free), 0% speed = level 10 (jammed)
                        if free_flow_speed > 0:
                            speed_ratio = current_speed / free_flow_speed
                            # Convert to 1-10 scale (inverted)
                            traffic_level = max(1, min(10, int(10 - (speed_ratio * 9))))
                        else:
                            traffic_level = 5

                        traffic_data = TrafficData(
                            region="moscow",
                            level=traffic_level,
                            description=f"Пробки {traffic_level} баллов",
                            timestamp=datetime.now()
                        )

                        # Update cache
                        _traffic_cache["moscow"] = traffic_data
                        _cache_timestamp = datetime.now()

                        logger.info("Got real traffic data from TomTom: level=%d (speed: %d/%d km/h)",
                                   traffic_level, current_speed, free_flow_speed)
                        return traffic_data
                    else:
                        logger.warning("TomTom API returned status %d, falling back to simulation", resp.status)
        except Exception as e:
            logger.warning("TomTom API failed: %s, falling back to simulation", e)

    # Fallback to simulated data
    traffic_level = _get_simulated_traffic_level()

    traffic_data = TrafficData(
        region="moscow",
        level=traffic_level,
        description=f"Пробки {traffic_level} баллов (симуляция)",
        timestamp=datetime.now()
    )

    # Update cache
    _traffic_cache["moscow"] = traffic_data
    _cache_timestamp = datetime.now()

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
        timestamp=datetime.now()
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
        timestamp=datetime.now()
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
