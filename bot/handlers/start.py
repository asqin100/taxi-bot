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
        should_choose_tariff = False

        logger.info(f"[START] Processing /start for user {user_id}")

        # Extract referral code from deep link
        if message.text and len(message.text.split()) > 1:
            referral_code = message.text.split()[1]

        try:
            logger.info(f"[START] Creating/fetching user {user_id}")
            async with session_factory() as session:
                result = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()
                if not user:
                    is_new_user = True
                    should_choose_tariff = True
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
                    logger.info(f"[START] Created new user {user_id}")
                else:
                    # Existing user but tariff not selected yet
                    if not getattr(user, "preferred_tariff", None):
                        should_choose_tariff = True
                        logger.info(f"[START] User {user_id} has no preferred_tariff, will ask")

            # If new user or missing tariff, ask to choose tariff right away
            if should_choose_tariff:
                from bot.keyboards.inline import tariff_selection_keyboard
                await send_and_cleanup(
                    message,
                    "🚗 <b>Выберите ваш тариф</b>\n\n"
                    "Этот тариф будет использоваться для показа коэффициентов и расчёта комиссии в Финансах.\n"
                    "Вы сможете изменить его позже в разделе: <b>Финансы → Мой тариф</b>.\n\n"
                    "Выберите тариф:",
                    reply_markup=tariff_selection_keyboard(current_tariff="econom"),
                    parse_mode="HTML",
                    delete_user_message=False,
                )
                return

            # Ensure financial settings exist for users (so admin panel sees them consistently)
            if is_new_user:
                try:
                    from bot.services import financial as fin_service
                    await fin_service.get_or_create_settings(user_id)
                except Exception:
                    logger.warning(f"[START] Failed to create financial settings for user {user_id}")
        except Exception as e:
            logger.error(f"[START] Error creating user: {e}", exc_info=True)
            raise

        # Process referral code for new users
        if is_new_user and referral_code:
            try:
                logger.info(f"[START] Processing referral code for user {user_id}")
                from bot.services.referral import register_referral
                success = await register_referral(user_id, referral_code)
                if success:
                    await message.answer(
                        "🎉 Вы зарегистрированы по реферальной ссылке!\n"
                        "Ваш реферер получит бонусы за ваши покупки."
                    )
            except Exception as e:
                logger.error(f"[START] Error processing referral: {e}", exc_info=True)
                # Continue even if referral fails

        # Get user subscription tier for menu
        try:
            logger.info(f"[START] Getting subscription for user {user_id}")
            from bot.services.subscription import get_subscription
            subscription = await get_subscription(user_id)
            logger.info(f"[START] Got subscription: tier={subscription.tier}")
        except Exception as e:
            logger.error(f"[START] Error getting subscription: {e}", exc_info=True)
            raise

        # Check if user should see onboarding
        try:
            logger.info(f"[START] Checking onboarding for user {user_id}")
            show_onboarding = await should_show_onboarding(user_id)
            logger.info(f"[START] Show onboarding: {show_onboarding}")
        except Exception as e:
            logger.error(f"[START] Error checking onboarding: {e}", exc_info=True)
            raise

        if show_onboarding:
            # Show onboarding for new users
            try:
                logger.info(f"[START] Showing onboarding to user {user_id}")
                step_data = get_onboarding_step("welcome")
                text = f"{step_data['title']}\n\n{step_data['text']}"

                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Начать обучение 🚀", callback_data="onboarding:coefficients")],
                    [InlineKeyboardButton(text="Пропустить", callback_data="onboarding:skip")],
                ])

                await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
                logger.info(f"[START] Sent onboarding to user {user_id}")
            except Exception as e:
                logger.error(f"[START] Error showing onboarding: {e}", exc_info=True)
                raise
        else:
            # Show regular welcome for returning users
            try:
                logger.info(f"[START] Showing main menu to user {user_id}")
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
                logger.info(f"[START] Sent main menu to user {user_id}")
            except Exception as e:
                logger.error(f"[START] Error showing main menu: {e}", exc_info=True)
                raise

    except Exception as e:
        logger.error(f"[START] FATAL ERROR for user {message.from_user.id}: {e}", exc_info=True)
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

    # Check if the message contains any media (can't edit_text on media messages)
    has_media = any([
        callback.message.photo,
        callback.message.document,
        callback.message.video,
        callback.message.audio,
        callback.message.animation,
        callback.message.voice,
        callback.message.video_note,
        callback.message.sticker
    ])

    if has_media:
        # Delete the media message and send a new text message
        await callback.message.delete()
        await callback.message.answer(
            "📋 Главное меню",
            reply_markup=main_menu_keyboard(subscription.tier),
        )
    else:
        # Regular text message - can edit
        await callback.message.edit_text(
            "📋 Главное меню",
            reply_markup=main_menu_keyboard(subscription.tier),
        )
    await callback.answer()
