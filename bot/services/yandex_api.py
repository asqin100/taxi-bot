"""
Сервис для работы с Яндекс API (Навигатор и Карты).
"""
from typing import Tuple
from urllib.parse import urlencode


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
