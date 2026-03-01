"""AI Advisor handler - intelligent recommendations."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.ai_advisor import get_smart_recommendation, format_recommendation
from bot.services.claude_api import ask_claude, get_advanced_recommendation
from bot.services.subscription import check_feature_access, get_user_subscription
from bot.services.message_manager import send_and_cleanup

router = Router()


class AskQuestion(StatesGroup):
    waiting_for_question = State()


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

    # Get recommendation with personal insights
    recommendation = await get_smart_recommendation(user_id=user_id)
    text = format_recommendation(recommendation)

    # Check if user has Premium for advanced features
    subscription = await get_user_subscription(user_id)

    keyboard_buttons = [
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="menu:advisor"),
            InlineKeyboardButton(text="🏆 ТОП-5", callback_data="cmd:top"),
        ]
    ]

    # Add "Ask Question" button for Premium users
    if subscription and subscription.tier == "premium":
        keyboard_buttons.append([
            InlineKeyboardButton(text="💬 Задать вопрос AI", callback_data="advisor:ask")
        ])

    keyboard_buttons.append([
        InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "advisor:ask")
async def cb_ask_question(callback: CallbackQuery, state: FSMContext):
    """Start asking a question to AI."""
    user_id = callback.from_user.id

    # Double-check Premium access
    subscription = await get_user_subscription(user_id)
    if not subscription or subscription.tier != "premium":
        await callback.answer("⚠️ Эта функция доступна только на Premium", show_alert=True)
        return

    text = (
        "💬 <b>ЗАДАТЬ ВОПРОС AI-СОВЕТНИКУ</b>\n\n"
        "Вы можете спросить о:\n"
        "  • Штрафах и правилах работы в такси\n"
        "  • Оптимизации заработка\n"
        "  • Лицензиях и документах\n"
        "  • ПДД и безопасности\n"
        "  • Расходах и налогах\n\n"
        "Напишите ваш вопрос:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu:advisor")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AskQuestion.waiting_for_question)
    await callback.answer()


@router.message(AskQuestion.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    """Process user's question to AI."""
    user_id = message.from_user.id
    question = message.text

    # Send "thinking" message
    thinking_msg = await message.answer("🤔 Анализирую ваш вопрос...")

    try:
        # Get answer from Claude
        answer = await ask_claude(question)

        # Delete thinking message
        await thinking_msg.delete()

        # Send answer
        text = f"💬 <b>ОТВЕТ AI-СОВЕТНИКА</b>\n\n{answer}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ещё вопрос", callback_data="advisor:ask")],
            [InlineKeyboardButton(text="◀️ К рекомендациям", callback_data="menu:advisor")],
        ])

        await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")

    except Exception as e:
        await thinking_msg.delete()
        await message.answer(
            "❌ Произошла ошибка при обработке вопроса. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:advisor")]
            ])
        )

    await state.clear()
