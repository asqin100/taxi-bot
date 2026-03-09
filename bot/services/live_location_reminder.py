"""Live Location expiration reminders."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from aiogram import Bot
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from bot.database.db import session_factory
from bot.models.user import User

logger = logging.getLogger(__name__)

# Send reminder 30 minutes before expiration
REMINDER_MINUTES_BEFORE = 30


async def check_live_location_expiration(bot: Bot):
    """Check for expiring Live Locations and send reminders."""
    try:
        now = datetime.now()
        reminder_threshold = now + timedelta(minutes=REMINDER_MINUTES_BEFORE)

        async with session_factory() as session:
            # Find users with Live Location expiring soon
            result = await session.execute(
                select(User).where(
                    User.geo_alerts_enabled == True,
                    User.live_location_expires_at.isnot(None),
                    User.live_location_expires_at <= reminder_threshold,
                    User.live_location_expires_at > now,
                )
            )
            users = result.scalars().all()

            for user in users:
                try:
                    # Calculate remaining time
                    remaining = (user.live_location_expires_at - now).total_seconds() / 60

                    if remaining <= REMINDER_MINUTES_BEFORE:
                        await _send_expiration_reminder(bot, user, remaining)

                        # Clear expiration time to avoid sending duplicate reminders
                        user.live_location_expires_at = None
                        await session.commit()

                except Exception as e:
                    logger.error(f"Error sending reminder to user {user.telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_live_location_expiration: {e}")


async def _send_expiration_reminder(bot: Bot, user: User, remaining_minutes: float):
    """Send reminder to user about expiring Live Location."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Продлить Live Location (8 часов)", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    text = (
        f"⏰ <b>НАПОМИНАНИЕ</b>\n\n"
        f"Ваша Live Location истекает через {int(remaining_minutes)} минут.\n\n"
        f"Чтобы продолжить получать геоалерты о высоких коэффициентах рядом с вами, "
        f"продлите Live Location на следующие 8 часов.\n\n"
        f"👇 Нажмите кнопку ниже:"
    )

    # Add inline keyboard with main menu button
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
    ])

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        # Send inline keyboard in a separate message to provide main menu access
        await bot.send_message(
            chat_id=user.telegram_id,
            text="Или вернитесь в главное меню:",
            reply_markup=inline_keyboard,
        )
        logger.info(f"Sent Live Location expiration reminder to user {user.telegram_id}")
    except Exception as e:
        logger.error(f"Failed to send reminder to {user.telegram_id}: {e}")
