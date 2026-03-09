"""
Сервис для работы с Яндекс API (Навигатор и Карты).
"""
import time
from dataclasses import dataclass, field
from typing import Tuple
from urllib.parse import urlencode

from bot.services.zones import Zone, get_zones


@dataclass
class SurgeData:
    zone_id: str
    tariff: str
    coefficient: float
    timestamp: float = field(default_factory=time.time)


class SurgeCache:
    """In-memory cache for surge coefficients."""

    def __init__(self, ttl: int = 120):
        self.ttl = ttl
        self._data: dict[tuple[str, str], SurgeData] = {}

    def get(self, zone_id: str, tariff: str) -> SurgeData | None:
        item = self._data.get((zone_id, tariff))
        if item and (time.time() - item.timestamp) < self.ttl:
            return item
        return None

    def set(self, data: SurgeData):
        self._data[(data.zone_id, data.tariff)] = data

    def get_all(self) -> list[SurgeData]:
        now = time.time()
        return [d for d in self._data.values() if (now - d.timestamp) < self.ttl]


# Global cache instance
cache = SurgeCache(ttl=150)


def generate_yandex_navigator_link(latitude: float, longitude: float, name: str = "") -> str:
    """
    Генерирует ссылку для открытия точки в Яндекс.Навигаторе.

    Args:
        latitude: Широта точки назначения
        longitude: Долгота точки назначения
        name: Название точки (опционально)

    Returns:
        URL для открытия в Яндекс.Навигаторе
    """
    # Формат: yandexnavi://build_route_on_map?lat_to=55.7558&lon_to=37.6173
    params = {
        'lat_to': latitude,
        'lon_to': longitude
    }

    return f"yandexnavi://build_route_on_map?{urlencode(params)}"


def generate_yandex_maps_link(latitude: float, longitude: float, name: str = "") -> str:
    """
    Генерирует ссылку для открытия точки в Яндекс.Картах.

    Args:
        latitude: Широта точки назначения
        longitude: Долгота точки назначения
        name: Название точки (опционально)

    Returns:
        URL для открытия в Яндекс.Картах
    """
    # Формат: https://yandex.ru/maps/?rtext=~55.7558,37.6173
    # rtext означает построение маршрута от текущей позиции до указанной точки
    return f"https://yandex.ru/maps/?rtext=~{latitude},{longitude}"


def generate_navigation_links(latitude: float, longitude: float, name: str = "") -> Tuple[str, str]:
    """
    Генерирует обе ссылки: для Навигатора и Карт.

    Args:
        latitude: Широта точки назначения
        longitude: Долгота точки назначения
        name: Название точки (опционально)

    Returns:
        Кортеж (ссылка_навигатор, ссылка_карты)
    """
    navigator_link = generate_yandex_navigator_link(latitude, longitude, name)
    maps_link = generate_yandex_maps_link(latitude, longitude, name)

    return navigator_link, maps_link


def get_cached_coefficients(tariff: str | None = None) -> list[SurgeData]:
    """Get cached surge coefficients, optionally filtered by tariff."""
    all_data = cache.get_all()
    if tariff:
        return [d for d in all_data if d.tariff == tariff]
    return all_data


def get_top_zones(n: int = 5, tariff: str | None = None) -> list[SurgeData]:
    """Get top N zones with highest coefficients."""
    data = get_cached_coefficients(tariff)
    data.sort(key=lambda x: x.coefficient, reverse=True)
    return data[:n]


async def fetch_all_coefficients() -> list[SurgeData]:
    """
    Fetch surge for all zones and tariffs, update cache.
    This is a placeholder that returns mock data.
    The actual fetching is done by coefficient_collector service.
    """
    # Return cached data if available
    return cache.get_all()
