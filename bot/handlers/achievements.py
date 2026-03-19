"""Achievements handler - gamification system."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.achievements import get_user_achievements, format_achievements_list
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("achievements"))
async def cmd_achievements(message: Message):
    """Show user achievements via command."""
    await _send_achievements(message)


@router.callback_query(F.data == "menu:achievements")
async def cb_achievements(callback: CallbackQuery):
    """Show user achievements via callback."""
    await _send_achievements(callback.message)
    await callback.answer()


async def _send_achievements(message: Message):
    """Send achievements list."""
    user_id = message.chat.id

    achievements = await get_user_achievements(user_id)
    text = format_achievements_list(achievements)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="menu:achievements")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
