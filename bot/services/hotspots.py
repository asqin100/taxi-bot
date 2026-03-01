"""Hotspots service - airports, train stations, and other high-demand locations."""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bot.services.yandex_api import get_cached_coefficients
from bot.services.traffic import get_moscow_traffic

logger = logging.getLogger(__name__)


@dataclass
class Hotspot:
    """High-demand location with surge and traffic info."""
    id: str
    name: str
    type: str  # airport, train_station, mall, stadium
    zone_id: str  # corresponding zone in moscow_zones.json
    description: str
    tips: list[str]

    # Dynamic data
    current_coefficient: float = 0.0
    traffic_level: int = 0
    recommendation: str = ""


# Airport definitions
AIRPORTS = [
    Hotspot(
        id="sheremetyevo",
        name="Шереметьево",
        type="airport",
        zone_id="sheremetyevo",
        description="Крупнейший аэропорт Москвы. Терминалы B, C, D, E, F.",
        tips=[
            "🅿️ Парковка: P1-P5, стоимость от 100₽/час",
            "📍 Зона ожидания: между терминалами B и C",
            "⏰ Пик: 6:00-9:00 и 18:00-22:00",
            "💡 Лучше брать заказы из терминалов D, E, F",
        ]
    ),
    Hotspot(
        id="domodedovo",
        name="Домодедово",
        type="airport",
        zone_id="domodedovo",
        description="Второй по величине аэропорт Москвы.",
        tips=[
            "🅿️ Парковка: P1-P4, первые 15 минут бесплатно",
            "📍 Зона ожидания: у выхода 3",
            "⏰ Пик: 5:00-8:00 и 17:00-21:00",
            "💡 Много международных рейсов = щедрые чаевые",
        ]
    ),
    Hotspot(
        id="vnukovo",
        name="Внуково",
        type="airport",
        zone_id="vnukovo",
        description="Третий по величине аэропорт Москвы.",
        tips=[
            "🅿️ Парковка: P1-P3, стоимость от 80₽/час",
            "📍 Зона ожидания: у терминала A",
            "⏰ Пик: 6:00-9:00 и 18:00-21:00",
            "💡 Меньше конкуренции, чем в Шереметьево",
        ]
    ),
]


# Train station definitions
TRAIN_STATIONS = [
    Hotspot(
        id="kazansky",
        name="Казанский вокзал",
        type="train_station",
        zone_id="center",
        description="Поезда в Казань, Нижний Новгород, Урал.",
        tips=[
            "📍 Зона ожидания: площадь трёх вокзалов",
            "⏰ Пик: утро (отправление) и вечер (прибытие)",
            "💡 Много багажа = хорошие чаевые",
        ]
    ),
    Hotspot(
        id="leningradsky",
        name="Ленинградский вокзал",
        type="train_station",
        zone_id="center",
        description="Поезда в Санкт-Петербург, Петрозаводск, Мурманск.",
        tips=[
            "📍 Зона ожидания: площадь трёх вокзалов",
            "⏰ Пик: утро и вечер (Сапсаны)",
            "💡 Бизнес-пассажиры = стабильный спрос",
        ]
    ),
    Hotspot(
        id="yaroslavsky",
        name="Ярославский вокзал",
        type="train_station",
        zone_id="center",
        description="Поезда в Ярославль, Вологду, Архангельск.",
        tips=[
            "📍 Зона ожидания: площадь трёх вокзалов",
            "⏰ Пик: утро и вечер",
            "💡 Рядом с метро Комсомольская",
        ]
    ),
]


async def get_hotspot_info(hotspot_id: str) -> Optional[Hotspot]:
    """Get detailed information about a specific hotspot."""
    # Find hotspot
    all_hotspots = AIRPORTS + TRAIN_STATIONS
    hotspot = next((h for h in all_hotspots if h.id == hotspot_id), None)

    if not hotspot:
        return None

    # Get current coefficient for this zone
    coefficients = get_cached_coefficients()
    zone_coeffs = [c for c in coefficients if c.zone_id == hotspot.zone_id]

    if zone_coeffs:
        # Get max coefficient across all tariffs
        hotspot.current_coefficient = max(c.coefficient for c in zone_coeffs)

    # Get traffic info
    traffic = await get_moscow_traffic()
    if traffic:
        hotspot.traffic_level = traffic.level

        # Generate recommendation
        if hotspot.current_coefficient >= 2.0 and traffic.level <= 5:
            hotspot.recommendation = "✅ Отличное время! Высокий кэф и нормальные дороги"
        elif hotspot.current_coefficient >= 2.0:
            hotspot.recommendation = "⚠️ Высокий кэф, но пробки. Закладывайте время"
        elif hotspot.current_coefficient < 1.5:
            hotspot.recommendation = "❌ Низкий кэф. Лучше поискать другие точки"
        else:
            hotspot.recommendation = "🟡 Средние условия"

    return hotspot


def get_all_airports() -> list[Hotspot]:
    """Get list of all airports."""
    return AIRPORTS.copy()


def get_all_train_stations() -> list[Hotspot]:
    """Get list of all train stations."""
    return TRAIN_STATIONS.copy()


def format_hotspot_info(hotspot: Hotspot) -> str:
    """Format hotspot information as text."""
    lines = []

    # Header with emoji
    emoji = "✈️" if hotspot.type == "airport" else "🚂"
    lines.append(f"{emoji} <b>{hotspot.name}</b>\n")

    # Description
    lines.append(f"<i>{hotspot.description}</i>\n")

    # Current conditions
    if hotspot.current_coefficient > 0:
        coef_emoji = "🔥" if hotspot.current_coefficient >= 2.0 else "⚡"
        lines.append(f"📊 <b>Коэффициент:</b> {coef_emoji} <code>x{hotspot.current_coefficient}</code>")

    if hotspot.traffic_level > 0:
        if hotspot.traffic_level <= 3:
            traffic_emoji = "🟢"
        elif hotspot.traffic_level <= 6:
            traffic_emoji = "🟡"
        else:
            traffic_emoji = "🔴"
        lines.append(f"🚦 <b>Пробки:</b> {traffic_emoji} {hotspot.traffic_level}/10")

    if hotspot.recommendation:
        lines.append(f"\n{hotspot.recommendation}\n")

    # Tips
    lines.append("<b>💡 Советы:</b>")
    for tip in hotspot.tips:
        lines.append(f"  {tip}")

    return "\n".join(lines)
