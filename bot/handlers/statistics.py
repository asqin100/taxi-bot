"""Statistics handler - show driver earnings statistics."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.financial import get_statistics

router = Router()


@router.callback_query(F.data == "menu_statistics")
async def cb_statistics_menu(callback: CallbackQuery) -> None:
    """Show statistics period selection menu"""
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 7 дней", callback_data="stats_7")
    builder.button(text="📈 14 дней", callback_data="stats_14")
    builder.button(text="💎 30 дней", callback_data="stats_30")
    builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
    builder.adjust(3, 1)

    text = (
        "📊 <b>Статистика заработка</b>\n\n"
        "Выберите период для анализа:"
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("stats_"))
async def cb_show_statistics(callback: CallbackQuery) -> None:
    """Display statistics for selected period"""
    days_str = callback.data.split("_")[1]
    days = int(days_str)

    # Get statistics using existing financial service
    stats = await get_statistics(callback.from_user.id, "custom")

    # Get shifts for the period to calculate stats
    from bot.services.financial import get_shifts_by_period
    shifts = await get_shifts_by_period(callback.from_user.id, days)

    if not shifts:
        text = f"📊 <b>Статистика за {days} дней</b>\n\n" \
               "Нет завершенных смен за выбранный период."
    else:
        total_hours = sum(s.duration_hours for s in shifts)
        gross = sum(s.gross_earnings for s in shifts)
        net = sum(s.net_earnings for s in shifts)
        distance = sum(s.distance_km for s in shifts)
        trips = sum(s.trips_count for s in shifts)

        avg_hourly = net / total_hours if total_hours > 0 else 0
        avg_per_shift = net / len(shifts) if shifts else 0

        best_shift = max(shifts, key=lambda s: s.net_earnings)
        worst_shift = min(shifts, key=lambda s: s.net_earnings)

        text = (
            f"📊 <b>Статистика за {days} дней</b>\n\n"
            f"🚕 Смен: {len(shifts)}\n"
            f"⏱ Часов: {total_hours:.1f}\n"
            f"🛣 Километров: {distance:.1f}\n"
            f"📍 Поездок: {trips}\n\n"
            f"💰 <b>Заработок:</b>\n"
            f"   Валовый: {gross:,.2f} ₽\n"
            f"   Чистый: {net:,.2f} ₽\n\n"
            f"📈 <b>Средние показатели:</b>\n"
            f"   В час: {avg_hourly:.2f} ₽\n"
            f"   За смену: {avg_per_shift:.2f} ₽\n\n"
            f"🏆 Лучшая смена: {best_shift.net_earnings:.2f} ₽\n"
            f"📉 Худшая смена: {worst_shift.net_earnings:.2f} ₽"
        )

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Другой период", callback_data="menu_statistics")
    builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
