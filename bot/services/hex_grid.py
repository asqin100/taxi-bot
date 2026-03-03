"""Hexagonal grid generation for Moscow surge coefficient map."""

import math
from dataclasses import dataclass

from bot.services.zones import get_zones
from bot.services.yandex_api import get_cached_coefficients

# Moscow bounding box
LAT_MIN, LAT_MAX = 55.4, 56.0
LON_MIN, LON_MAX = 37.2, 38.0

# Hex size in degrees (~1.2 km)
HEX_SIZE = 0.015


@dataclass
class HexCell:
    center_lat: float
    center_lon: float
    vertices: list[list[float]]  # [[lat, lon], ...]
    coefficient: float
    color: str


# Precomputed cos(lat) for longitude correction (set once in generate)
_COS_LAT: float = 1.0


def _flat_top_hex_vertices(cx: float, cy: float, size: float) -> list[list[float]]:
    """Return 6 vertices of a flat-top hexagon centered at (cx, cy).

    Uses shared _COS_LAT so all hexagons use the same projection,
    ensuring edges align perfectly with no gaps.
    """
    lon_size = size / _COS_LAT
    verts = []
    for i in range(6):
        angle = math.radians(60 * i)
        lat = cx + size * math.sin(angle)
        lon = cy + lon_size * math.cos(angle)
        verts.append([round(lat, 6), round(lon, 6)])
    return verts


def _purple_color(coeff: float) -> str:
    """Map coefficient to purple palette rgba string with better visibility."""
    # 1.0 -> light lavender, 2.5+ -> deep purple
    t = min(max((coeff - 1.0) / 1.5, 0.0), 1.0)  # 0..1 for range 1.0..2.5 (narrower for better visibility)
    # Interpolate from light lavender to deep purple
    r = int(220 - 140 * t)  # 220 -> 80
    g = int(200 - 180 * t)  # 200 -> 20
    b = int(255 - 55 * t)   # 255 -> 200
    a = round(0.35 + 0.55 * t, 2)  # 0.35 -> 0.90 (much more visible even at low coefficients)
    return f"rgba({r},{g},{b},{a})"


def _purple_hex_color(coeff: float) -> str:
    """Map coefficient to hex color for Pillow (no alpha)."""
    t = min(max((coeff - 1.0) / 1.0, 0.0), 1.0)
    r = int(200 - 120 * t)
    g = int(180 - 160 * t)
    b = int(255 - 55 * t)
    return f"#{r:02x}{g:02x}{b:02x}"


def _purple_alpha(coeff: float) -> int:
    """Map coefficient to alpha 0-255 for Pillow."""
    t = min(max((coeff - 1.0) / 1.0, 0.0), 1.0)
    return int(64 + 140 * t)  # 64..204


def _assign_coefficient(lat: float, lon: float, surge_map: dict[str, float]) -> float:
    """Find nearest zone and assign its coefficient with distance falloff."""
    zones = get_zones()
    best_coeff = 1.0
    best_weight = 0.0

    for zone in zones:
        dlat = lat - zone.lat
        dlon = (lon - zone.lon) * math.cos(math.radians(lat))
        dist_km = math.sqrt(dlat**2 + dlon**2) * 111.32
        radius = zone.radius_km

        coeff = surge_map.get(zone.id, 1.0)
        if coeff <= 1.0:
            continue

        if dist_km <= radius:
            weight = 1.0
        elif dist_km <= radius * 2:
            weight = 1.0 - (dist_km - radius) / radius
        else:
            continue

        if weight * coeff > best_weight * best_coeff if best_weight > 0 else True:
            best_coeff = coeff
            best_weight = weight

    if best_weight <= 0:
        return 1.0
    # Apply falloff
    return round(1.0 + (best_coeff - 1.0) * best_weight, 2)


def generate_hex_grid(tariff: str | None = None) -> list[HexCell]:
    """Generate hex grid with coefficients from cached data.

    Uses offset coordinates for flat-top hexagons.
    Columns go along lon axis, rows along lat axis.
    Odd columns are shifted down (south) by half a row height.
    """
    data = get_cached_coefficients(tariff)
    surge_map: dict[str, float] = {}
    for sd in data:
        if sd.zone_id not in surge_map or sd.coefficient > surge_map[sd.zone_id]:
            surge_map[sd.zone_id] = sd.coefficient

    # For flat-top hex with circumradius R (center to vertex = HEX_SIZE):
    # Column spacing (lon direction): 1.5 * R
    # Row spacing (lat direction):    sqrt(3) * R
    # Odd columns offset by:          sqrt(3)/2 * R  (in lat direction)
    row_step = HEX_SIZE * math.sqrt(3)
    half_row = row_step / 2

    # Use center latitude for lon correction — shared with vertex function
    global _COS_LAT
    center_lat_rad = math.radians((LAT_MIN + LAT_MAX) / 2)
    _COS_LAT = math.cos(center_lat_rad)
    col_step_lon = HEX_SIZE * 1.5 / _COS_LAT

    cells: list[HexCell] = []
    col = 0
    lon = LON_MIN
    while lon <= LON_MAX:
        # Odd columns shift lat by +half_row
        lat_offset = half_row if (col % 2 == 1) else 0.0
        lat = LAT_MIN + lat_offset
        while lat <= LAT_MAX:
            coeff = _assign_coefficient(lat, lon, surge_map)
            if coeff > 1.0:
                verts = _flat_top_hex_vertices(lat, lon, HEX_SIZE)
                cells.append(HexCell(
                    center_lat=lat,
                    center_lon=lon,
                    vertices=verts,
                    coefficient=coeff,
                    color=_purple_color(coeff),
                ))
            lat += row_step
        lon += col_step_lon
        col += 1

    return cells


def hex_grid_json(tariff: str | None = None) -> list[dict]:
    """Return hex grid as JSON-serializable list."""
    cells = generate_hex_grid(tariff)
    return [
        {
            "vertices": c.vertices,
            "coefficient": c.coefficient,
            "color": c.color,
        }
        for c in cells
    ]
