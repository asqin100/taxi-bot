from datetime import datetime

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.keyboards.inline import main_menu_keyboard, tariff_keyboard
from bot.services.message_manager import send_and_cleanup
from bot.services.onboarding import should_show_onboarding, get_onboarding_step
from bot.config import settings
from bot.handlers.promo_code import PromoCodeStates
from bot.database.db import get_session
from bot.models.promo_code import PromoCodeUsage
from sqlalchemy import select, func as sa_func


async def _has_any_promo_usage(user_id: int) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(sa_func.count()).select_from(PromoCodeUsage).where(PromoCodeUsage.user_id == user_id)
        )
        return (result.scalar_one() or 0) > 0


async def _has_beta_access(user_id: int) -> bool:
    # Admin bypass is handled outside.
    # Requirement: entered promo once -> access forever.
    return await _has_any_promo_usage(user_id)


async def _prompt_for_invite_promo(message: Message, state: FSMContext) -> None:
    await state.set_state(PromoCodeStates.waiting_for_code)
    await send_and_cleanup(
        message,
        "🔒 <b>Бета-доступ</b>\n\n"
        "Для входа в бот введите <b>пригласительный промокод</b> (он даёт максимальную подписку).\n\n"
        "Отправьте код сообщением:",
        parse_mode="HTML",
        delete_user_message=False,
    )
    return


def _needs_beta_gate() -> bool:
    return bool(settings.restrict_beta_gate)


def _admin_ids() -> set[int]:
    return {int(x.strip()) for x in (settings.admin_ids or "").split(",") if x.strip()}


def _is_admin(user_id: int) -> bool:
    return user_id in _admin_ids()


async def _ensure_beta_access_or_prompt(message: Message, state: FSMContext) -> bool:
    """Return True if access is allowed, otherwise prompt for invite promo code and return False."""
    if not _needs_beta_gate():
        return True

    user_id = message.from_user.id
    if _is_admin(user_id):
        return True

    if await _has_beta_access(user_id):
        return True

    await _prompt_for_invite_promo(message, state)
    return False


async def _ensure_beta_access_or_prompt_callback(callback: CallbackQuery) -> bool:
    """Same check for callback-only entrypoints (no FSM prompt)."""
    if not _needs_beta_gate():
        return True

    user_id = callback.from_user.id
    if _is_admin(user_id):
        return True

    if await _has_beta_access(user_id):
        return True

    await callback.answer("🔒 Нужен пригласительный промокод. Нажмите /start", show_alert=True)
    return False



router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    import logging
    logger = logging.getLogger(__name__)

    try:
        user_id = message.from_user.id
        is_new_user = False
        referral_code = None
        should_choose_tariff = False

        logger.info(f"[START] Processing /start for user {user_id}")

        if not await _ensure_beta_access_or_prompt(message, state):
            return

        # Extract referral code from deep link
        if message.text and len(message.text.split()) > 1:
            referral_code = message.text.split()[1]

        try:
            logger.info(f"[START] Creating/fetching user {user_id}")
            async with session_factory() as session:
                # Optimized: Single query to get user
                result = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()

                if not user:
                    is_new_user = True
                    should_choose_tariff = True
                    # Generate referral code for new user
                    from bot.services.referral import generate_referral_code

                    # Optimized: Generate code once, rely on unique constraint
                    code = generate_referral_code()

                    # Optimized: Use INSERT OR IGNORE pattern to handle race conditions
                    user = User(
                        telegram_id=user_id,
                        username=message.from_user.username,
                        referral_code=code,
                        created_at=datetime.now(),
                    )
                    session.add(user)

                    try:
                        await session.commit()
                        logger.info(f"[START] Created new user {user_id}")
                    except Exception as e:
                        # If unique constraint fails (rare race condition), fetch existing user
                        await session.rollback()
                        result = await session.execute(
                            select(User).where(User.telegram_id == user_id)
                        )
                        user = result.scalar_one_or_none()
                        if not user:
                            raise  # Re-raise if it's a different error
                        is_new_user = False
                        logger.info(f"[START] User {user_id} already exists (race condition)")
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

        # Enforce invite promo gate (entered once -> access forever)
        if settings.restrict_beta_gate and (not _is_admin(user_id)) and (not await _has_beta_access(user_id)):
            await _prompt_for_invite_promo(message, state)
            return

        # Ensure user always has at least a free subscription record
        try:
            subscription = await get_subscription(user_id)
        except Exception as e:
            logger.error(f"[START] Error ensuring subscription: {e}", exc_info=True)
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
    if not await _ensure_beta_access_or_prompt_callback(callback):
        return
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
