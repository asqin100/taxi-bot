"""Leaderboard handler - anonymous rankings interface."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.leaderboard import (
    get_earnings_leaderboard,
    get_hours_leaderboard,
    get_efficiency_leaderboard,
    format_leaderboard
)
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("leaderboard"))
async def cmd_leaderboard(message: Message):
    """Show leaderboard via command."""
    await _send_leaderboard(message, "earnings", "week")


@router.callback_query(F.data == "menu:leaderboard")
async def cb_leaderboard(callback: CallbackQuery):
    """Show leaderboard via callback."""
    await _send_leaderboard(callback.message, "earnings", "week")
    await callback.answer()


@router.callback_query(F.data.startswith("leaderboard:"))
async def cb_leaderboard_filter(callback: CallbackQuery):
    """Handle leaderboard filter changes."""
    parts = callback.data.split(":")
    metric = parts[1]  # earnings, hours, efficiency
    period = parts[2] if len(parts) > 2 else "week"  # week, month, all

    await _send_leaderboard(callback.message, metric, period)
    await callback.answer()


async def _send_leaderboard(message: Message, metric: str = "earnings", period: str = "week"):
    """Send leaderboard with filters."""
    user_id = message.chat.id

    # Show loading
    if hasattr(message, 'edit_text'):
        await message.edit_text("📊 Загружаю рейтинг...")
    else:
        processing_msg = await message.answer("📊 Загружаю рейтинг...")

    # Get leaderboard data
    if metric == "earnings":
        entries = await get_earnings_leaderboard(period=period, limit=10, user_id=user_id)
    elif metric == "hours":
        entries = await get_hours_leaderboard(period=period, limit=10, user_id=user_id)
    else:  # efficiency
        entries = await get_efficiency_leaderboard(period=period, limit=10, user_id=user_id)

    if not entries:
        text = "📊 <b>Рейтинг</b>\n\nНедостаточно данных для отображения рейтинга."
    else:
        text = format_leaderboard(entries, metric, period)

    # Create keyboard with filters
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💰 Заработок" if metric == "earnings" else "💰",
                callback_data="leaderboard:earnings:week"
            ),
            InlineKeyboardButton(
                text="⏱ Часы" if metric == "hours" else "⏱",
                callback_data="leaderboard:hours:week"
            ),
            InlineKeyboardButton(
                text="⚡ Эффективность" if metric == "efficiency" else "⚡",
                callback_data="leaderboard:efficiency:week"
            ),
        ],
        [
            InlineKeyboardButton(
                text="📅 Неделя" if period == "week" else "Неделя",
                callback_data=f"leaderboard:{metric}:week"
            ),
            InlineKeyboardButton(
                text="📅 Месяц" if period == "month" else "Месяц",
                callback_data=f"leaderboard:{metric}:month"
            ),
        ],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    if hasattr(message, 'edit_text'):
        await message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await processing_msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
