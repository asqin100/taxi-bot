"""AI Advisor handler - intelligent recommendations."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.ai_advisor import get_smart_recommendation, format_recommendation
from bot.services.claude_api import ask_claude, get_advanced_recommendation
from bot.services.subscription import check_feature_access, get_user_subscription
from bot.services.message_manager import send_and_cleanup, split_long_message
from bot.services.ai_usage import check_can_ask, increment_usage, get_usage_stats

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

    # Check AI usage limits
    can_ask, current_usage, daily_limit = await check_can_ask(user_id)

    if not can_ask:
        await callback.answer(
            f"⚠️ Вы исчерпали дневной лимит вопросов ({daily_limit}/день)\n"
            f"Попробуйте завтра!",
            show_alert=True
        )
        return

    remaining = daily_limit - current_usage

    text = (
        "💬 <b>ЗАДАТЬ ВОПРОС AI-СОВЕТНИКУ</b>\n\n"
        "Вы можете спросить о:\n"
        "  • Штрафах и правилах работы в такси\n"
        "  • Оптимизации заработка\n"
        "  • Лицензиях и документах\n"
        "  • ПДД и безопасности\n"
        "  • Расходах и налогах\n\n"
        f"📊 Осталось вопросов сегодня: <b>{remaining}/{daily_limit}</b>\n\n"
        "Напишите ваш вопрос:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu:advisor")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AskQuestion.waiting_for_question)
    await callback.answer()


@router.message(AskQuestion.waiting_for_question)
async def process_question(message: Message, state: FSMContext):
    """Process user's question to AI."""
    user_id = message.from_user.id
    question = message.text

    # Check limits again (in case user waited too long)
    can_ask, current_usage, daily_limit = await check_can_ask(user_id)

    if not can_ask:
        await message.answer(
            f"⚠️ Вы исчерпали дневной лимит вопросов ({daily_limit}/день)\n"
            f"Попробуйте завтра!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:advisor")]
            ])
        )
        await state.clear()
        return

    # Send "thinking" message
    thinking_msg = await message.answer("🤔 Анализирую ваш вопрос...")

    try:
        # Get answer from Gemini
        answer = await ask_claude(question)

        # Increment usage counter
        await increment_usage(user_id)

        # Get updated stats
        stats = await get_usage_stats(user_id)

        # Delete thinking message
        await thinking_msg.delete()

        # Prepare full text
        full_text = f"💬 <b>ОТВЕТ AI-СОВЕТНИКА</b>\n\n{answer}"

        # Split if too long
        chunks = split_long_message(full_text, max_length=4000)

        # Add usage info to keyboard
        remaining_text = f"📊 {stats['remaining']}/{stats['limit']}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"💬 Ещё вопрос ({remaining_text})", callback_data="advisor:ask")],
            [InlineKeyboardButton(text="◀️ К рекомендациям", callback_data="menu:advisor")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
        ])

        # Send all chunks
        for i, chunk in enumerate(chunks):
            # Only add keyboard to the last message
            if i == len(chunks) - 1:
                await send_and_cleanup(message, chunk, reply_markup=keyboard, parse_mode="HTML")
            else:
                await message.answer(chunk, parse_mode="HTML")

    except Exception as e:
        await thinking_msg.delete()
        await message.answer(
            "❌ Произошла ошибка при обработке вопроса. Попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:advisor")]
            ])
        )

    await state.clear()
