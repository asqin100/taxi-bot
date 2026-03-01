import json
from dataclasses import dataclass
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "moscow_zones.json"


@dataclass
class Zone:
    id: str
    name: str
    lat: float
    lon: float
    radius_km: float


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
