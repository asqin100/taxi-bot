"""Geocoding service using Yandex Geocoder API."""
import logging
from typing import Optional

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)


async def geocode_address(address: str) -> Optional[tuple[float, float]]:
    """
    Convert address to coordinates using Yandex Geocoder.

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    if not settings.yandex_geocoder_key:
        logger.warning("Yandex Geocoder API key not configured")
        return None

    try:
        url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": settings.yandex_geocoder_key,
            "geocode": address,
            "format": "json",
            "results": 1,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    logger.warning("Geocoder API returned status %d", resp.status)
                    return None

                data = await resp.json()

                # Parse response
                try:
                    geo_object = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                    pos = geo_object["Point"]["pos"]
                    lon, lat = map(float, pos.split())

                    logger.info("Geocoded '%s' to (%.6f, %.6f)", address, lat, lon)
                    return (lat, lon)

                except (KeyError, IndexError, ValueError) as e:
                    logger.warning("Failed to parse geocoder response: %s", e)
                    return None

    except Exception as e:
        logger.error("Geocoding failed for '%s': %s", address, e)
        return None


def find_nearest_zone(lat: float, lon: float, zones: list) -> Optional[str]:
    """
    Find the nearest zone to given coordinates.

    Args:
        lat: Latitude
        lon: Longitude
        zones: List of Zone objects with center_lat, center_lon

    Returns:
        Zone ID of the nearest zone
    """
    import math

    def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth radius in km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)

        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    if not zones:
        return None

    nearest_zone = None
    min_distance = float('inf')

    for zone in zones:
        dist = distance(lat, lon, zone.center_lat, zone.center_lon)
        if dist < min_distance:
            min_distance = dist
            nearest_zone = zone.id

    logger.info("Nearest zone to (%.6f, %.6f) is %s (%.2f km)", lat, lon, nearest_zone, min_distance)
    return nearest_zone
