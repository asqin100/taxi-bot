"""Geocoding service using Yandex Geocoder API and Nominatim fallback."""
import logging
from typing import Optional

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)


async def geocode_address(address: str) -> Optional[tuple[float, float]]:
    """
    Convert address to coordinates using Yandex Geocoder or Nominatim fallback.

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    # Try Yandex Geocoder first if API key is available
    if settings.yandex_geocoder_key:
        coords = await _geocode_yandex(address)
        if coords:
            return coords
        logger.info("Yandex geocoding failed, trying Nominatim fallback")

    # Fallback to Nominatim (OpenStreetMap)
    return await _geocode_nominatim(address)


async def _geocode_yandex(address: str) -> Optional[tuple[float, float]]:
    """Geocode using Yandex Geocoder API."""
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
                    logger.warning("Yandex Geocoder returned status %d", resp.status)
                    return None

                data = await resp.json()

                # Parse response
                try:
                    geo_object = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
                    pos = geo_object["Point"]["pos"]
                    lon, lat = map(float, pos.split())

                    logger.info("Yandex geocoded '%s' to (%.6f, %.6f)", address, lat, lon)
                    return (lat, lon)

                except (KeyError, IndexError, ValueError) as e:
                    logger.warning("Failed to parse Yandex response: %s", e)
                    return None

    except Exception as e:
        logger.error("Yandex geocoding failed for '%s': %s", address, e)
        return None


async def _geocode_nominatim(address: str) -> Optional[tuple[float, float]]:
    """Geocode using Nominatim (OpenStreetMap) - free, no API key required."""
    try:
        # Try multiple search strategies
        search_queries = [
            address,  # Original query
            f"{address}, Москва",  # With Moscow
            f"{address}, Московская область",  # With Moscow Oblast
            f"{address}, Россия",  # With Russia
        ]

        headers = {
            "User-Agent": "TaxiBot/1.0"  # Nominatim requires User-Agent
        }

        async with aiohttp.ClientSession() as session:
            for search_query in search_queries:
                try:
                    url = "https://nominatim.openstreetmap.org/search"
                    params = {
                        "q": search_query,
                        "format": "json",
                        "limit": 1,
                        "addressdetails": 1,
                        "countrycodes": "ru",  # Limit to Russia
                    }

                    async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status != 200:
                            continue

                        data = await resp.json()

                        if data:
                            result = data[0]
                            lat = float(result["lat"])
                            lon = float(result["lon"])

                            logger.info("Nominatim geocoded '%s' (query: '%s') to (%.6f, %.6f)",
                                       address, search_query, lat, lon)
                            return (lat, lon)

                except Exception as e:
                    logger.debug("Failed to geocode with query '%s': %s", search_query, e)
                    continue

            logger.info("Nominatim found no results for '%s' with any query variant", address)
            return None

    except Exception as e:
        logger.error("Nominatim geocoding failed for '%s': %s", address, e)
        return None


def find_nearest_zone(lat: float, lon: float, zones: list) -> Optional[str]:
    """
    Find the nearest zone to given coordinates.

    Args:
        lat: Latitude
        lon: Longitude
        zones: List of Zone objects with lat, lon

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
        dist = distance(lat, lon, zone.lat, zone.lon)
        if dist < min_distance:
            min_distance = dist
            nearest_zone = zone.id

    logger.info("Nearest zone to (%.6f, %.6f) is %s (%.2f km)", lat, lon, nearest_zone, min_distance)
    return nearest_zone
