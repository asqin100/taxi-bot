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
    import logging
    logger = logging.getLogger(__name__)

    try:
        user_id = message.from_user.id
        is_new_user = False
        referral_code = None

        # Extract referral code from deep link
        if message.text and len(message.text.split()) > 1:
            referral_code = message.text.split()[1]

        async with session_factory() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                is_new_user = True
                # Generate referral code for new user
                from bot.services.referral import generate_referral_code

                # Ensure unique code
                while True:
                    code = generate_referral_code()
                    existing = await session.execute(
                        select(User).where(User.referral_code == code)
                    )
                    if not existing.scalar_one_or_none():
                        break

                user = User(
                    telegram_id=user_id,
                    username=message.from_user.username,
                    referral_code=code,
                )
                session.add(user)
                await session.commit()

        # Process referral code for new users
        if is_new_user and referral_code:
            from bot.services.referral import register_referral
            success = await register_referral(user_id, referral_code)
            if success:
                await message.answer(
                    "🎉 Вы зарегистрированы по реферальной ссылке!\n"
                    "Ваш реферер получит бонусы за ваши покупки."
                )

        # Get user subscription tier for menu
        from bot.services.subscription import get_subscription
        subscription = await get_subscription(user_id)

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
                reply_markup=main_menu_keyboard(subscription.tier),
            )
    except Exception as e:
        logger.error(f"Error in cmd_start for user {message.from_user.id}: {e}", exc_info=True)
        # Send a simple error message to user
        try:
            await message.answer("Произошла ошибка. Попробуйте позже или обратитесь в поддержку.")
        except:
            pass


@router.callback_query(F.data == "cmd:menu")
async def cb_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Get user subscription tier for menu
    from bot.services.subscription import get_subscription
    subscription = await get_subscription(user_id)

    await callback.message.edit_text(
        "📋 Главное меню",
        reply_markup=main_menu_keyboard(subscription.tier),
    )
    await callback.answer()
