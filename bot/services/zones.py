import json
import math
from dataclasses import dataclass
from pathlib import Path

from typing import Optional, Tuple, List

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "moscow_zones.json"
METRO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "moscow_metro.json"


@dataclass
class Zone:
    id: str
    name: str
    lat: float
    lon: float
    radius_km: float


@dataclass
class ZoneWithCoefficient:
    """Zone with surge coefficient and distance from user."""
    zone: Zone
    coefficient: float
    distance_km: float
    tariff: str


_zones: list[Zone] | None = None


def get_zones() -> list[Zone]:
    global _zones
    if _zones is None:
        with open(DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _zones = [Zone(**z) for z in data["zones"]]
    return _zones


def get_zone_by_id(zone_id: str) -> Zone | None:
    for z in get_zones():
        if z.id == zone_id:
            return z
    return None


def get_zone_names_map() -> dict[str, str]:
    return {z.id: z.name for z in get_zones()}


def load_metro_stations() -> List[dict]:
    """Load Moscow metro stations from JSON file."""
    try:
        if METRO_PATH.exists():
            with open(METRO_PATH, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("stations", [])
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to load metro stations: {e}")
    return []


def find_nearest_metro(zone_lat: float, zone_lon: float) -> Optional[Tuple[str, float]]:
    """
    Find nearest metro station to the specified zone center.

    Args:
        zone_lat: Zone center latitude
        zone_lon: Zone center longitude

    Returns:
        Tuple (station name, distance in km) or None
    """
    stations = load_metro_stations()
    if not stations:
        return None

    nearest_station = None
    min_distance = float('inf')

    for station in stations:
        distance = calculate_distance(zone_lat, zone_lon, station['lat'], station['lon'])
        if distance < min_distance:
            min_distance = distance
            nearest_station = station['name']

    return (nearest_station, min_distance) if nearest_station else None


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points using Haversine formula.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in kilometers
    """
    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))

    return R * c


def find_nearest_high_coefficient_zone(
    user_lat: float,
    user_lon: float,
    surge_data: list,
    min_coefficient: float = 1.3,
    max_distance_km: float = 5.0,
    tariff: str = "econom"
) -> ZoneWithCoefficient | None:
    """
    Find nearest zone with high coefficient within specified radius.

    Args:
        user_lat: User's latitude
        user_lon: User's longitude
        surge_data: List of SurgeData objects from yandex_api
        min_coefficient: Minimum coefficient threshold (default 1.3)
        max_distance_km: Maximum search radius in km (default 5.0)
        tariff: Tariff to filter by (default "econom")

    Returns:
        ZoneWithCoefficient or None if no suitable zone found
    """
    zones = get_zones()
    suitable_zones = []

    # Filter surge data by tariff and coefficient
    high_coeff_zones = {
        sd.zone_id: sd.coefficient
        for sd in surge_data
        if sd.tariff == tariff and sd.coefficient >= min_coefficient
    }

    if not high_coeff_zones:
        return None

    # Find zones within distance and with high coefficient
    for zone in zones:
        if zone.id not in high_coeff_zones:
            continue

        distance = calculate_distance(user_lat, user_lon, zone.lat, zone.lon)

        if distance <= max_distance_km:
            suitable_zones.append(ZoneWithCoefficient(
                zone=zone,
                coefficient=high_coeff_zones[zone.id],
                distance_km=distance,
                tariff=tariff
            ))

    # Sort by distance and return nearest
    if suitable_zones:
        suitable_zones.sort(key=lambda z: z.distance_km)
        return suitable_zones[0]

    return None
