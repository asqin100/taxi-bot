"""
Сервис для работы с зонами и поиска зон с высокими коэффициентами.
"""
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple
import math


@dataclass
class ZoneInfo:
    """Информация о зоне с коэффициентом."""
    zone_id: str
    tariff: str
    coefficient: float
    distance_km: float
    latitude: float
    longitude: float


# Координаты зон (в реальном проекте должны храниться в БД)
ZONE_COORDINATES = {
    "zone_1": (55.7558, 37.6173),  # Москва, центр
    "zone_2": (55.7522, 37.6156),
    "zone_3": (55.7539, 37.6208),
    "center": (55.7558, 37.6173),
    "airport": (55.9726, 37.4146),  # Шереметьево
}


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Вычисляет расстояние между двумя точками по координатам (формула гаверсинусов).

    Args:
        lat1, lon1: Координаты первой точки
        lat2, lon2: Координаты второй точки

    Returns:
        Расстояние в километрах
    """
    R = 6371  # Радиус Земли в км

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
    conn: sqlite3.Connection,
    user_lat: float,
    user_lon: float,
    min_coefficient: float = 1.3,
    max_distance_km: float = 5.0,
    tariff: str = "econom"
) -> Optional[ZoneInfo]:
    """
    Находит ближайшую зону с коэффициентом >= min_coefficient в радиусе max_distance_km.

    Args:
        conn: Подключение к базе данных
        user_lat: Широта пользователя
        user_lon: Долгота пользователя
        min_coefficient: Минимальный коэффициент (по умолчанию 1.3)
        max_distance_km: Максимальное расстояние в км (по умолчанию 5.0)
        tariff: Тариф для поиска (по умолчанию "econom")

    Returns:
        ZoneInfo с информацией о зоне или None, если не найдено
    """
    cursor = conn.cursor()

    # Получаем последние коэффициенты для всех зон
    cursor.execute("""
        SELECT DISTINCT zone_id, coefficient
        FROM coefficient_history
        WHERE tariff = ?
        AND timestamp >= datetime('now', '-1 hour')
        ORDER BY timestamp DESC
    """, (tariff,))

    zones_with_coef = {}
    for row in cursor.fetchall():
        zone_id = row[0]
        coefficient = row[1]
        if zone_id not in zones_with_coef:
            zones_with_coef[zone_id] = coefficient

    # Фильтруем зоны по коэффициенту и расстоянию
    suitable_zones = []

    for zone_id, coefficient in zones_with_coef.items():
        if coefficient < min_coefficient:
            continue

        if zone_id not in ZONE_COORDINATES:
            continue

        zone_lat, zone_lon = ZONE_COORDINATES[zone_id]
        distance = calculate_distance(user_lat, user_lon, zone_lat, zone_lon)

        if distance <= max_distance_km:
            suitable_zones.append(ZoneInfo(
                zone_id=zone_id,
                tariff=tariff,
                coefficient=coefficient,
                distance_km=distance,
                latitude=zone_lat,
                longitude=zone_lon
            ))

    # Сортируем по расстоянию и возвращаем ближайшую
    if suitable_zones:
        suitable_zones.sort(key=lambda z: z.distance_km)
        return suitable_zones[0]

    return None


def get_all_high_coefficient_zones(
    conn: sqlite3.Connection,
    user_lat: float,
    user_lon: float,
    min_coefficient: float = 1.3,
    max_distance_km: float = 5.0,
    limit: int = 5
) -> List[ZoneInfo]:
    """
    Получает список всех зон с высоким коэффициентом в радиусе.

    Args:
        conn: Подключение к базе данных
        user_lat: Широта пользователя
        user_lon: Долгота пользователя
        min_coefficient: Минимальный коэффициент
        max_distance_km: Максимальное расстояние в км
        limit: Максимальное количество зон

    Returns:
        Список ZoneInfo, отсортированный по расстоянию
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT zone_id, coefficient
        FROM coefficient_history
        WHERE tariff = 'econom'
        AND timestamp >= datetime('now', '-1 hour')
        ORDER BY timestamp DESC
    """)

    zones_with_coef = {}
    for row in cursor.fetchall():
        zone_id = row[0]
        coefficient = row[1]
        if zone_id not in zones_with_coef:
            zones_with_coef[zone_id] = coefficient

    suitable_zones = []

    for zone_id, coefficient in zones_with_coef.items():
        if coefficient < min_coefficient:
            continue

        if zone_id not in ZONE_COORDINATES:
            continue

        zone_lat, zone_lon = ZONE_COORDINATES[zone_id]
        distance = calculate_distance(user_lat, user_lon, zone_lat, zone_lon)

        if distance <= max_distance_km:
            suitable_zones.append(ZoneInfo(
                zone_id=zone_id,
                tariff="econom",
                coefficient=coefficient,
                distance_km=distance,
                latitude=zone_lat,
                longitude=zone_lon
            ))

    suitable_zones.sort(key=lambda z: z.distance_km)
    return suitable_zones[:limit]
