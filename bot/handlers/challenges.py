"""Challenge handler - weekly challenges interface."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.challenges import get_or_create_weekly_challenge, get_challenge_stats, format_challenge
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("challenge"))
async def cmd_challenge(message: Message):
    """Show current weekly challenge via command."""
    await _send_challenge(message)


@router.callback_query(F.data == "menu:challenge")
async def cb_challenge(callback: CallbackQuery):
    """Show current weekly challenge via callback."""
    await _send_challenge(callback.message)
    await callback.answer()


async def _send_challenge(message: Message):
    """Send current weekly challenge."""
    user_id = message.chat.id

    # Get current challenge
    challenge = await get_or_create_weekly_challenge(user_id)
    stats = await get_challenge_stats(user_id)

    text = "🏆 <b>НЕДЕЛЬНЫЙ ЧЕЛЛЕНДЖ</b>\n\n"
    text += format_challenge(challenge)

    if stats["has_history"]:
        text += f"\n\n📊 Всего завершено: {stats['total_completed']}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="menu:challenge")],
        [InlineKeyboardButton(text="🏅 Достижения", callback_data="menu:achievements")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
