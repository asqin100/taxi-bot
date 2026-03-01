"""AI Advisor service - intelligent recommendations for drivers."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from collections import Counter

from bot.services.yandex_api import get_cached_coefficients, get_top_zones
from bot.services.traffic import get_moscow_traffic
from bot.services.zones import get_zone_by_id
from bot.database.db import get_session
from bot.models.shift import Shift
from sqlalchemy import select, func

logger = logging.getLogger(__name__)


class Recommendation:
    """AI recommendation with reasoning."""
    def __init__(self, text: str, confidence: str, reasoning: list[str], personal_insights: list[str] = None):
        self.text = text
        self.confidence = confidence  # high, medium, low
        self.reasoning = reasoning
        self.personal_insights = personal_insights or []


async def _get_user_shift_stats(user_id: int, days: int = 30) -> dict:
    """
    Analyze user's shift history for personalized insights.

    Returns:
        Dict with statistics: best_hours, best_days, avg_hourly_rate, total_shifts
    """
    async with get_session() as session:
        # Get shifts from last N days
        cutoff_date = datetime.now() - timedelta(days=days)

        result = await session.execute(
            select(Shift).where(
                Shift.user_id == user_id,
                Shift.end_time.isnot(None),
                Shift.start_time >= cutoff_date
            )
        )
        shifts = result.scalars().all()

        if not shifts:
            return {
                "total_shifts": 0,
                "best_hours": [],
                "best_days": [],
                "avg_hourly_rate": 0,
                "has_history": False
            }

        # Analyze best hours (by hourly rate)
        hour_rates = {}
        for shift in shifts:
            hour = shift.start_time.hour
            if hour not in hour_rates:
                hour_rates[hour] = []
            hour_rates[hour].append(shift.hourly_rate)

        # Calculate average rate per hour
        hour_avg = {h: sum(rates) / len(rates) for h, rates in hour_rates.items()}
        best_hours = sorted(hour_avg.items(), key=lambda x: x[1], reverse=True)[:3]

        # Analyze best days of week
        day_rates = {}
        for shift in shifts:
            day = shift.start_time.weekday()  # 0=Monday, 6=Sunday
            if day not in day_rates:
                day_rates[day] = []
            day_rates[day].append(shift.hourly_rate)

        day_avg = {d: sum(rates) / len(rates) for d, rates in day_rates.items()}
        best_days = sorted(day_avg.items(), key=lambda x: x[1], reverse=True)[:2]

        # Overall average
        avg_rate = sum(s.hourly_rate for s in shifts) / len(shifts)

        return {
            "total_shifts": len(shifts),
            "best_hours": [h for h, _ in best_hours],
            "best_days": [d for d, _ in best_days],
            "avg_hourly_rate": avg_rate,
            "has_history": True,
            "hour_rates": hour_avg,
            "day_rates": day_avg
        }


def _get_day_name(day: int) -> str:
    """Get Russian day name from weekday number."""
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    return days[day]


async def _generate_personal_insights(user_id: int, current_hour: int, current_day: int) -> list[str]:
    """Generate personalized insights based on user's history."""
    stats = await _get_user_shift_stats(user_id, days=30)

    if not stats["has_history"]:
        return []

    insights = []

    # Check if current hour is in user's best hours
    if current_hour in stats["best_hours"]:
        rank = stats["best_hours"].index(current_hour) + 1
        insights.append(f"⭐ Это ваш #{rank} лучший час по заработку!")

    # Check if current day is in user's best days
    if current_day in stats["best_days"]:
        day_name = _get_day_name(current_day)
        insights.append(f"📅 {day_name.capitalize()} — один из ваших лучших дней")

    # Compare with average
    if stats["hour_rates"].get(current_hour):
        hour_rate = stats["hour_rates"][current_hour]
        if hour_rate > stats["avg_hourly_rate"] * 1.2:
            insights.append(f"💰 В этот час вы обычно зарабатываете {hour_rate:.0f} руб/ч")

    # Shift count insight
    if stats["total_shifts"] >= 10:
        insights.append(f"📊 Анализ основан на {stats['total_shifts']} сменах за месяц")

    return insights


async def get_smart_recommendation(user_id: Optional[int] = None) -> Recommendation:
    """
    Analyze current conditions and provide intelligent recommendation.

    Considers:
    - Current coefficients across zones
    - Traffic conditions
    - Time of day
    - Day of week
    - User's personal shift history (if user_id provided)
    """
    now = datetime.now()
    hour = now.hour
    is_weekend = now.weekday() >= 5
    current_day = now.weekday()

    # Get current data
    coefficients = get_cached_coefficients()
    traffic = await get_moscow_traffic()
    top_zones = get_top_zones(3)

    reasoning = []
    personal_insights = []

    # Get personal insights if user_id provided
    if user_id:
        personal_insights = await _generate_personal_insights(user_id, hour, current_day)

    # Analyze time of day
    if 6 <= hour < 10:
        time_factor = "morning_rush"
        reasoning.append("🌅 Утренний час-пик: высокий спрос на поездки")
    elif 10 <= hour < 17:
        time_factor = "midday"
        reasoning.append("☀️ Дневное время: средний спрос")
    elif 17 <= hour < 21:
        time_factor = "evening_rush"
        reasoning.append("🌆 Вечерний час-пик: пиковый спрос")
    elif 21 <= hour < 24:
        time_factor = "evening"
        reasoning.append("🌙 Вечер: спрос снижается")
    else:
        time_factor = "night"
        reasoning.append("🌃 Ночь: низкий спрос, но высокие коэффициенты")

    # Analyze weekend
    if is_weekend:
        reasoning.append("📅 Выходной: другие паттерны спроса")

    # Analyze coefficients
    if not coefficients:
        return Recommendation(
            text="❌ Нет данных о коэффициентах. Попробуйте позже.",
            confidence="low",
            reasoning=["⚠️ Данные не загружены"]
        )

    avg_coef = sum(c.coefficient for c in coefficients) / len(coefficients)
    max_coef = max(c.coefficient for c in coefficients)

    if max_coef >= 2.5:
        reasoning.append(f"🔥 Очень высокие коэффициенты (до x{max_coef:.1f})")
    elif max_coef >= 2.0:
        reasoning.append(f"🔥 Высокие коэффициенты (до x{max_coef:.1f})")
    elif max_coef >= 1.5:
        reasoning.append(f"⚡ Средние коэффициенты (до x{max_coef:.1f})")
    else:
        reasoning.append(f"📉 Низкие коэффициенты (до x{max_coef:.1f})")

    # Analyze traffic
    if traffic:
        if traffic.level <= 3:
            reasoning.append(f"🟢 Дороги свободны ({traffic.level}/10)")
        elif traffic.level <= 6:
            reasoning.append(f"🟡 Средние пробки ({traffic.level}/10)")
        else:
            reasoning.append(f"🔴 Серьёзные пробки ({traffic.level}/10)")

    # Generate recommendation
    recommendation_text, confidence = _generate_recommendation(
        time_factor=time_factor,
        is_weekend=is_weekend,
        max_coef=max_coef,
        avg_coef=avg_coef,
        traffic_level=traffic.level if traffic else 5,
        top_zones=top_zones
    )

    return Recommendation(
        text=recommendation_text,
        confidence=confidence,
        reasoning=reasoning,
        personal_insights=personal_insights
    )


def _generate_recommendation(
    time_factor: str,
    is_weekend: bool,
    max_coef: float,
    avg_coef: float,
    traffic_level: int,
    top_zones: list
) -> tuple[str, str]:
    """Generate recommendation based on analyzed factors."""

    # Excellent conditions
    if max_coef >= 2.0 and traffic_level <= 5:
        if time_factor in ["morning_rush", "evening_rush"]:
            zone_names = ", ".join([get_zone_by_id(z.zone_id).name for z in top_zones[:2]])
            return (
                f"✅ <b>ОТЛИЧНОЕ ВРЕМЯ ДЛЯ РАБОТЫ!</b>\n\n"
                f"Высокие коэффициенты и нормальные дороги. "
                f"Рекомендую работать в зонах: <b>{zone_names}</b>",
                "high"
            )
        else:
            return (
                f"✅ <b>ХОРОШИЕ УСЛОВИЯ</b>\n\n"
                f"Коэффициенты высокие, дороги свободны. "
                f"Можно работать, но спрос может быть ниже из-за времени суток.",
                "medium"
            )

    # High coefficients but bad traffic
    if max_coef >= 2.0 and traffic_level > 7:
        return (
            f"⚠️ <b>ВЫСОКИЕ КОЭФФИЦИЕНТЫ, НО ПРОБКИ</b>\n\n"
            f"Заработок будет хороший, но готовьтесь к задержкам. "
            f"Закладывайте больше времени на поездки.",
            "medium"
        )

    # Low coefficients and bad traffic
    if max_coef < 1.5 and traffic_level > 7:
        return (
            f"❌ <b>НЕ РЕКОМЕНДУЕТСЯ</b>\n\n"
            f"Низкие коэффициенты и пробки. "
            f"Лучше подождать или поискать другие зоны.",
            "low"
        )

    # Night time with high coefficients
    if time_factor == "night" and max_coef >= 2.0:
        return (
            f"🌃 <b>НОЧНАЯ РАБОТА ВЫГОДНА</b>\n\n"
            f"Высокие ночные коэффициенты и свободные дороги. "
            f"Хорошее время для тех, кто работает ночью.",
            "high"
        )

    # Weekend with medium conditions
    if is_weekend and avg_coef >= 1.5:
        return (
            f"📅 <b>ВЫХОДНОЙ ДЕНЬ</b>\n\n"
            f"Средние условия. Спрос есть, но паттерны отличаются от будних дней. "
            f"Следите за событиями (концерты, матчи).",
            "medium"
        )

    # Default: average conditions
    return (
        f"🟡 <b>СРЕДНИЕ УСЛОВИЯ</b>\n\n"
        f"Можно работать, но заработок будет средним. "
        f"Следите за изменением коэффициентов.",
        "medium"
    )


async def get_zone_recommendation(zone_id: str) -> Optional[str]:
    """Get recommendation for a specific zone."""
    zone = get_zone_by_id(zone_id)
    if not zone:
        return None

    coefficients = get_cached_coefficients()
    zone_coeffs = [c for c in coefficients if c.zone_id == zone_id]

    if not zone_coeffs:
        return "Нет данных по этой зоне"

    max_coef = max(c.coefficient for c in zone_coeffs)
    traffic = await get_moscow_traffic()

    if max_coef >= 2.0 and traffic and traffic.level <= 5:
        return f"✅ Отличная зона! Коэф x{max_coef:.1f}, дороги свободны"
    elif max_coef >= 2.0:
        return f"⚠️ Высокий коэф x{max_coef:.1f}, но пробки"
    elif max_coef >= 1.5:
        return f"🟡 Средний коэф x{max_coef:.1f}"
    else:
        return f"❌ Низкий коэф x{max_coef:.1f}, не рекомендуется"


def format_recommendation(rec: Recommendation) -> str:
    """Format recommendation as text."""
    lines = ["🤖 <b>AI-СОВЕТНИК</b>\n"]

    lines.append(rec.text)
    lines.append("\n<b>Анализ условий:</b>")

    for reason in rec.reasoning:
        lines.append(f"  {reason}")

    # Personal insights
    if rec.personal_insights:
        lines.append("\n<b>Персональная статистика:</b>")
        for insight in rec.personal_insights:
            lines.append(f"  {insight}")

    # Confidence indicator
    if rec.confidence == "high":
        lines.append("\n💪 <b>Уверенность:</b> Высокая")
    elif rec.confidence == "medium":
        lines.append("\n🤔 <b>Уверенность:</b> Средняя")
    else:
        lines.append("\n⚠️ <b>Уверенность:</b> Низкая")

    return "\n".join(lines)
