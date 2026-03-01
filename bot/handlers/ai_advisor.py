"""AI Advisor handler - intelligent recommendations."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.ai_advisor import get_smart_recommendation, format_recommendation
from bot.services.subscription import check_feature_access
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("advisor"))
async def cmd_advisor(message: Message):
    """Get AI recommendation via command."""
    await _send_advisor(message)


@router.callback_query(F.data == "menu:advisor")
async def cb_advisor(callback: CallbackQuery):
    """Get AI recommendation via callback."""
    await _send_advisor(callback.message)
    await callback.answer()


async def _send_advisor(message: Message):
    """Send AI advisor recommendation."""
    user_id = message.chat.id

    # Check if user has access to AI advisor
    has_access = await check_feature_access(user_id, "ai_advisor")

    if not has_access:
        text = (
            "🤖 <b>AI-СОВЕТНИК</b>\n\n"
            "⭐ Эта функция доступна только на тарифах <b>Pro</b> и <b>Premium</b>.\n\n"
            "AI-советник анализирует:\n"
            "  • Текущие коэффициенты\n"
            "  • Дорожную обстановку\n"
            "  • Время суток и день недели\n"
            "  • Исторические паттерны\n\n"
            "И даёт персональные рекомендации для максимального заработка."
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⬆️ Улучшить тариф", callback_data="subscription:upgrade")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
        ])

        await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
        return

    # Get recommendation
    recommendation = await get_smart_recommendation()
    text = format_recommendation(recommendation)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu:advisor"),
            InlineKeyboardButton(text="🏆 ТОП-5", callback_data="cmd:top"),
        ],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
