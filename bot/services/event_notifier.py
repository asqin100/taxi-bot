"""Event notification service."""
import logging
from datetime import datetime

from aiogram import Bot

from bot.services import events as event_service
from bot.services.yandex_api import get_cached_coefficients
from bot.services.zones import get_zones
from bot.services.notification_utils import is_quiet_hours
from bot.database.db import session_factory
from bot.models.user import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def check_and_notify_events(bot: Bot):
    """Check for events that need notifications and send alerts."""
    # Check for pre-notifications (20 min before end)
    pre_events = await event_service.get_events_for_pre_notification()
    for event in pre_events:
        await send_pre_notification(bot, event)
        await event_service.mark_pre_notified(event.id)

    # Check for end notifications
    end_events = await event_service.get_events_for_end_notification()
    for event in end_events:
        await send_end_notification(bot, event)
        await event_service.mark_end_notified(event.id)


async def send_pre_notification(bot: Bot, event):
    """Send pre-notification (20 min before event ends)."""
    emoji = {
        "concert": "🎵",
        "sport": "⚽",
        "conference": "🎤",
        "theater": "🎭",
        "other": "📍",
    }.get(event.event_type, "📍")

    time_str = event.end_time.strftime("%H:%M")

    # Get zone name
    zones = get_zones()
    zone_name = next((z.name for z in zones if z.id == event.zone_id), event.zone_id)

    text = (
        f"⏰ <b>Скоро закончится мероприятие!</b>\n\n"
        f"{emoji} <b>{event.name}</b>\n"
        f"📍 Зона: {zone_name}\n"
        f"⏰ Окончание: {time_str}\n\n"
        f"💡 Ожидается высокий спрос на такси!"
    )

    await send_to_users_by_event_type(bot, text, event.event_type)
    logger.info("Sent pre-notification for event: %s (type: %s)", event.name, event.event_type)


async def send_end_notification(bot: Bot, event):
    """Send notification when event ends."""
    emoji = {
        "concert": "🎵",
        "sport": "⚽",
        "conference": "🎤",
        "theater": "🎭",
        "other": "📍",
    }.get(event.event_type, "📍")

    # Get current coefficient for this zone
    coeffs = get_cached_coefficients()
    zone_coeffs = [c for c in coeffs if c.zone_id == event.zone_id]

    max_coeff = 1.0
    if zone_coeffs:
        max_coeff = max(c.coefficient for c in zone_coeffs)

    # Get zone name
    zones = get_zones()
    zone_name = next((z.name for z in zones if z.id == event.zone_id), event.zone_id)

    coeff_emoji = "🔥" if max_coeff >= 2.0 else "📈" if max_coeff >= 1.5 else "📊"

    text = (
        f"🎉 <b>Мероприятие закончилось!</b>\n\n"
        f"{emoji} <b>{event.name}</b>\n"
        f"📍 Зона: {zone_name}\n"
        f"{coeff_emoji} Коэффициент: <b>x{max_coeff:.2f}</b>\n\n"
        f"💰 Самое время работать в этой зоне!"
    )

    await send_to_users_by_event_type(bot, text, event.event_type)
    logger.info("Sent end notification for event: %s (type: %s, coeff: %.2f)", event.name, event.event_type, max_coeff)


async def send_to_users_by_event_type(bot: Bot, text: str, event_type: str):
    """Send message to users who have notifications enabled for this event type."""
    async with session_factory() as session:
        stmt = select(User).where(User.event_notify_enabled == True)
        result = await session.execute(stmt)
        users = result.scalars().all()

        sent_count = 0
        skipped_quiet = 0
        for user in users:
            # Check quiet hours
            if is_quiet_hours(user):
                skipped_quiet += 1
                continue

            # Check if user wants notifications for this event type
            user_event_types = [t.strip() for t in user.event_types.split(",") if t.strip()]

            if event_type in user_event_types:
                try:
                    await bot.send_message(user.telegram_id, text, parse_mode="HTML")
                    sent_count += 1
                except Exception as e:
                    logger.warning("Failed to send notification to user %d: %s", user.telegram_id, e)

        logger.info("Sent event notification to %d users (event type: %s, skipped %d in quiet hours)",
                   sent_count, event_type, skipped_quiet)


async def send_to_all_users(bot: Bot, text: str):
    """Send message to all users with notifications enabled (legacy function for coefficient alerts)."""
    async with session_factory() as session:
        stmt = select(User).where(User.notify_enabled == True)
        result = await session.execute(stmt)
        users = result.scalars().all()

        sent_count = 0
        skipped_quiet = 0
        for user in users:
            # Check quiet hours
            if is_quiet_hours(user):
                skipped_quiet += 1
                continue

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="HTML")
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to send notification to user %d: %s", user.telegram_id, e)

        logger.info("Sent notification to %d users (skipped %d in quiet hours)", sent_count, skipped_quiet)
