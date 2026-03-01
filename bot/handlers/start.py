from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.keyboards.inline import main_menu_keyboard, tariff_keyboard
from bot.services.message_manager import send_and_cleanup
from bot.services.onboarding import should_show_onboarding, get_onboarding_step

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    is_new_user = False

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            is_new_user = True
            user = User(
                telegram_id=user_id,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()

    # Check if user should see onboarding
    if await should_show_onboarding(user_id):
        # Show onboarding for new users
        step_data = get_onboarding_step("welcome")
        text = f"{step_data['title']}\n\n{step_data['text']}"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Начать обучение 🚀", callback_data="onboarding:coefficients")],
            [InlineKeyboardButton(text="Пропустить", callback_data="onboarding:skip")],
        ])

        await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
    else:
        # Show regular welcome for returning users
        await send_and_cleanup(
            message,
            "👋 С возвращением!\n\n"
            "Используйте меню ниже для навигации.\n\n"
            "💡 Новые функции:\n"
            "🏆 Челленджи и рейтинг\n"
            "🤖 AI-советник с персональными рекомендациями\n"
            "📊 Прогноз пробок на час вперед",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == "cmd:menu")
async def cb_menu(callback: CallbackQuery):
    await send_and_cleanup(
        callback.message,
        "📋 Главное меню",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()
