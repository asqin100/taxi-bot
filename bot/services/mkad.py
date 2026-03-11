"""MKAD (Moscow Ring Road) polygon coordinates and utilities."""
from typing import Tuple


# MKAD approximate polygon coordinates (clockwise from north)
# These are approximate coordinates of the Moscow Ring Road
MKAD_POLYGON = [
    (55.9167, 37.4333),  # North-West
    (55.9500, 37.5500),  # North
    (55.9500, 37.7000),  # North-East
    (55.9000, 37.8500),  # East-North
    (55.8000, 37.9000),  # East
    (55.6500, 37.8500),  # East-South
    (55.5700, 37.7500),  # South-East
    (55.5500, 37.6000),  # South
    (55.5700, 37.4500),  # South-West
    (55.6500, 37.3500),  # West-South
    (55.7500, 37.3000),  # West
    (55.8500, 37.3500),  # West-North
]


def point_in_polygon(lat: float, lon: float, polygon: list[Tuple[float, float]]) -> bool:
    """
    Check if a point is inside a polygon using ray casting algorithm.

    Args:
        lat: Point latitude
        lon: Point longitude
        polygon: List of (lat, lon) tuples defining polygon vertices

    Returns:
        True if point is inside polygon, False otherwise
    """
    n = len(polygon)
    inside = False

    p1_lat, p1_lon = polygon[0]
    for i in range(1, n + 1):
        p2_lat, p2_lon = polygon[i % n]

        if lon > min(p1_lon, p2_lon):
            if lon <= max(p1_lon, p2_lon):
                if lat <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        x_intersection = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    if p1_lat == p2_lat or lat <= x_intersection:
                        inside = not inside

        p1_lat, p1_lon = p2_lat, p2_lon

    return inside


def is_inside_mkad(lat: float, lon: float) -> bool:
    """
    Check if coordinates are inside Moscow Ring Road (MKAD).

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        True if inside MKAD, False otherwise
    """
    return point_in_polygon(lat, lon, MKAD_POLYGON)
