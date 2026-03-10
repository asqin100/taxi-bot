"""
Сервис для работы с Яндекс API (Навигатор, Карты и коэффициенты).
"""
import asyncio
import logging
import random
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Tuple
from urllib.parse import urlencode

import aiohttp

from bot.config import settings
from bot.services.zones import Zone, get_zones

logger = logging.getLogger(__name__)

TARIFFS = ["econom", "comfort", "business"]


@dataclass
class SurgeData:
    zone_id: str
    tariff: str
    coefficient: float
    timestamp: float = field(default_factory=time.time)


class BasePriceProvider(ABC):
    @abstractmethod
    async def fetch_surge(self, zone: Zone, tariff: str) -> float:
        """Return surge coefficient for a given zone and tariff."""


class YandexGoPassengerProvider(BasePriceProvider):
    """Yandex.Go passenger app API provider - more reliable than Pro API."""

    ROUTESTATS_URL = "https://tc.mobile.yandex.net/3.0/routestats"

    def _build_headers(self) -> dict:
        headers = {
            "accept-encoding": "gzip",
            "accept-language": "ru-RU",
            "content-type": "application/json; charset=utf-8",
            "user-agent": "yandex-taxi/5.63.1.127773 Android/15 (Xiaomi; 23013PC75G)",
        }
        if settings.yandex_bearer_token:
            headers["authorization"] = f"Bearer {settings.yandex_bearer_token}"
            headers["x-oauth-token"] = settings.yandex_bearer_token
        if settings.yandex_device_id:
            headers["x-appmetrica-deviceid"] = settings.yandex_device_id
        if settings.yandex_uuid:
            headers["x-appmetrica-uuid"] = settings.yandex_uuid
        if settings.yandex_mob_id:
            headers["x-mob-id"] = settings.yandex_mob_id
        return headers

    def _build_url(self) -> str:
        return (
            self.ROUTESTATS_URL
            + "?mobcf=russia%25go_ru_by_geo_hosts_3%25default"
            + "&mobpr=go_ru_by_geo_hosts_3_TAXI_0"
        )

    async def fetch_surge(self, zone: Zone, tariff: str) -> float:
        """Fetch surge coefficient using Yandex.Go passenger API."""
        # Create a short route within the zone
        dest_lat = zone.lat + 0.01
        dest_lon = zone.lon + 0.01

        body = {
            "id": uuid.uuid4().hex,
            "zone_name": "moscow",
            "selected_class": tariff,
            "route": [
                [zone.lon, zone.lat],
                [dest_lon, dest_lat],
            ],
            "tariff_requirements": [{"class": t} for t in TARIFFS],
            "force_soon_order": False,
            "payment": {"type": "card"},
            "skip_estimated_waiting": False,
            "use_toll_roads": False,
            "is_lightweight": False,
            "supports_paid_options": True,
            "format_currency": True,
            "supports_explicit_antisurge": True,
            "supports_multiclass": True,
            "summary_version": 2,
            "extended_description": True,
            "with_title": True,
            "account_type": "yandex",
        }

        # Retry logic for 429 errors
        max_retries = 2
        retry_delay = 10

        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession(headers=self._build_headers()) as session:
                    async with session.post(
                        self._build_url(),
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return self._extract_surge_coefficient(data, tariff)
                        elif resp.status == 429 and attempt < max_retries:
                            logger.warning(
                                "Rate limited (429) for zone %s, retrying in %ds (attempt %d/%d)",
                                zone.id, retry_delay, attempt + 1, max_retries
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        else:
                            error_body = await resp.text()
                            logger.warning(
                                "Yandex.Go API returned %s for zone %s: %s",
                                resp.status, zone.id, error_body[:500]
                            )
            except Exception as e:
                logger.error("Yandex.Go API error for zone %s: %s", zone.id, e)

        return 1.0

    @staticmethod
    def _extract_surge_coefficient(data: dict, tariff: str) -> float:
        """Extract surge coefficient from routestats response."""
        try:
            # Look for service_levels with paid_options.value
            for level in data.get("service_levels", []):
                if level.get("class") == tariff:
                    paid = level.get("paid_options", {})
                    if paid and "value" in paid:
                        coeff = float(paid["value"])
                        logger.info(
                            "Found surge %.2f for tariff %s",
                            coeff, tariff
                        )
                        return coeff

            # Fallback: try any tariff
            for level in data.get("service_levels", []):
                paid = level.get("paid_options", {})
                if paid and "value" in paid:
                    return float(paid["value"])

        except Exception as e:
            logger.warning("Failed to parse surge coefficient: %s", e)

        return 1.0


class YandexGoProvider(BasePriceProvider):
    """Real Yandex Pro API provider based on intercepted mobile API requests."""

    ROUTESTATS_URL = "https://tc.mobile.yandex.net/3.0/routestats"
    SURGE_MAP_URL = "https://taximeter.yandex.rostaxi.org/surge/map_meta"

    def _build_headers(self) -> dict:
        headers = {
            "accept": "application/json",
            "accept-encoding": "gzip",
            "accept-language": "ru",
            "user-agent": "app:pro brand:yandex version:13.38 build:24299 platform:android platform_version:15",
            "version": "13.38 (5024299)",
            "x-version-split": "13.38 (5024299)",
        }
        if settings.yandex_bearer_token:
            headers["authorization"] = f"Bearer {settings.yandex_bearer_token}"
        if settings.yandex_device_id:
            headers["x-appmetrica-deviceid"] = settings.yandex_device_id
        if settings.yandex_mob_id:
            headers["x-mob-id"] = settings.yandex_mob_id
        return headers

    def _build_url(self) -> str:
        return (
            self.ROUTESTATS_URL
            + "?mobcf=russia%25yandex_pro_ru_0%25default"
            + "&mobpr=yandex_pro_ru_0_Y_BASE_API_0"
        )

    def _build_surge_map_url(self, zone_id: str) -> str:
        """Build URL for surge map metadata endpoint."""
        params = (
            f"?hash=ucgj0"
            f"&device_id={settings.yandex_device_id}"
            f"&park_id=188d620a9be74ef18f156718fe56721d"
            f"&mobcf=russia%25yandex_pro_ru_0%25default"
            f"&mobpr=yandex_pro_ru_0_Y_BASE_API_0"
        )
        return self.SURGE_MAP_URL + params

    async def fetch_surge(self, zone: Zone, tariff: str) -> float:
        dest_lat = zone.lat + 0.01
        dest_lon = zone.lon + 0.01
        body = {
            "id": uuid.uuid4().hex,
            "zone_name": zone.id,
            "selected_class": tariff,
            "route": [
                [zone.lon, zone.lat],
                [dest_lon, dest_lat],
            ],
            "tariff_requirements": [{"class": t} for t in TARIFFS],
            "force_soon_order": False,
            "payment": {
                "type": "card",
            },
            "skip_estimated_waiting": False,
            "use_toll_roads": False,
            "is_lightweight": False,
            "supports_paid_options": True,
            "format_currency": True,
            "supports_explicit_antisurge": True,
            "supports_multiclass": True,
            "summary_version": 2,
            "extended_description": True,
            "with_title": True,
            "account_type": "yandex",
        }

        # Retry logic for 429 errors
        max_retries = 2
        retry_delay = 10

        for attempt in range(max_retries + 1):
            try:
                async with aiohttp.ClientSession(headers=self._build_headers()) as session:
                    async with session.post(
                        self._build_url(),
                        json=body,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return self._extract_surge(data, tariff)
                        elif resp.status == 429 and attempt < max_retries:
                            logger.warning(
                                "Rate limited (429) for zone %s, retrying in %ds (attempt %d/%d)",
                                zone.id, retry_delay, attempt + 1, max_retries
                            )
                            await asyncio.sleep(retry_delay)
                            continue
                        body_text = await resp.text()
                        logger.warning(
                            "Yandex API returned %s for zone %s: %s",
                            resp.status, zone.id, body_text[:200],
                        )
            except Exception as e:
                logger.error("Yandex API error for zone %s: %s", zone.id, e)
        return 1.0

    @staticmethod
    def _extract_surge(data: dict, tariff: str) -> float:
        """Extract surge coefficient from routestats response.

        The response contains service_levels with paid_options.value
        representing the surge multiplier. We look for the matching tariff class.
        """
        try:
            for level in data.get("service_levels", []):
                # Match the tariff class
                if level.get("class") == tariff:
                    paid = level.get("paid_options", {})
                    if paid and "value" in paid:
                        coeff = float(paid["value"])
                        logger.debug(
                            "Found surge %.2f for tariff %s (balance: %s)",
                            coeff,
                            tariff,
                            level.get("widget", {}).get("payload", {}).get("balance", "N/A")
                        )
                        return coeff

            # Fallback: if no matching tariff, try to get any surge value
            for level in data.get("service_levels", []):
                paid = level.get("paid_options", {})
                if paid and "value" in paid:
                    return float(paid["value"])
        except (KeyError, IndexError, TypeError, ValueError) as e:
            logger.warning("Failed to parse surge from response: %s", e)
        return 1.0


class MockProvider(BasePriceProvider):
    """Generates realistic mock surge data for development."""

    async def fetch_surge(self, zone: Zone, tariff: str) -> float:
        base = random.uniform(0.9, 1.1)
        # Airports and center tend to have higher surge
        if zone.id in ("sheremetyevo", "domodedovo", "vnukovo", "center"):
            base += random.uniform(0.2, 1.0)
        if tariff == "business":
            base += random.uniform(0.0, 0.3)
        return round(max(1.0, base), 1)


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


# Global instances
_provider: BasePriceProvider = YandexGoPassengerProvider() if settings.yandex_bearer_token else MockProvider()
cache = SurgeCache(ttl=settings.parse_interval_seconds + 30)


def set_provider(provider: BasePriceProvider):
    global _provider
    _provider = provider


async def fetch_all_coefficients() -> list[SurgeData]:
    """Fetch surge for all zones and tariffs, update cache.

    Uses controlled parallelism with batching to avoid rate limiting.
    Batch size: 5 concurrent requests, 2s delay between batches.
    """
    zones = get_zones()
    results: list[SurgeData] = []

    # Create list of all (zone, tariff) combinations
    tasks = [(zone, tariff) for zone in zones for tariff in TARIFFS]

    # Process in batches to avoid overwhelming the API
    batch_size = 5
    batch_delay = 2  # seconds between batches

    logger.info("Starting coefficient fetch: %d zones × %d tariffs = %d requests in batches of %d",
                len(zones), len(TARIFFS), len(tasks), batch_size)

    for i in range(0, len(tasks), batch_size):
        batch = tasks[i:i + batch_size]

        # Fetch batch concurrently
        batch_results = await asyncio.gather(
            *[_fetch_one(zone, tariff) for zone, tariff in batch],
            return_exceptions=True
        )

        # Process results
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error("Batch fetch error: %s", result)
                continue
            results.append(result)
            cache.set(result)

        # Delay between batches (except for last batch)
        if i + batch_size < len(tasks):
            await asyncio.sleep(batch_delay)

    logger.info("Fetched %d surge data points in %d batches", len(results), (len(tasks) + batch_size - 1) // batch_size)
    return results


async def _fetch_one(zone: Zone, tariff: str) -> SurgeData:
    coeff = await _provider.fetch_surge(zone, tariff)
    return SurgeData(zone_id=zone.id, tariff=tariff, coefficient=coeff)


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


def generate_yandex_navigator_link(latitude: float, longitude: float, name: str = "") -> str:
    """
    Генерирует ссылку для открытия точки в Яндекс.Навигаторе.

    Args:
        latitude: Широта точки назначения
        longitude: Долгота точки назначения
        name: Название точки (опционально)

    Returns:
        URL для открытия в Яндекс.Навигаторе (HTTPS для совместимости с Telegram)
    """
    # Используем HTTPS ссылку вместо yandexnavi:// для совместимости с Telegram inline buttons
    # Формат: https://yandex.ru/navi/?rtext=~lat,lon
    # Откроет приложение Навигатора если установлено, иначе веб-версию
    return f"https://yandex.ru/navi/?rtext=~{latitude},{longitude}"


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
