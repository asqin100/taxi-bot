"""Event notification service."""
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    logger.info("Checking for events that need notifications...")

    # Check for pre-notifications (20 min before end)
    pre_events = await event_service.get_events_for_pre_notification()
    logger.info("Found %d events needing pre-notification", len(pre_events))

    for event in pre_events:
        logger.info("Sending pre-notification for event: %s (ends at %s)", event.name, event.end_time)
        await send_pre_notification(bot, event)
        await event_service.mark_pre_notified(event.id)

    # Check for end notifications
    end_events = await event_service.get_events_for_end_notification()
    logger.info("Found %d events needing end notification", len(end_events))

    for event in end_events:
        logger.info("Sending end notification for event: %s (ended at %s)", event.name, event.end_time)
        await send_end_notification(bot, event)
        await event_service.mark_end_notified(event.id)


async def send_pre_notification(bot: Bot, event):
    """Send pre-notification (20 min before event ends) - only for Pro/Premium/Elite users."""
    emoji = {
        "concert": "🎵",
        "sport": "⚽",
        "conference": "🎤",
        "theater": "🎭",
        "other": "📍",
    }.get(event.event_type, "📍")

    time_str = event.end_time.strftime("%H:%M")

    # Use venue name if available, otherwise fall back to zone name
    location_name = event.venue_name
    if not location_name:
        zones = get_zones()
        zone = next((z for z in zones if z.id == event.zone_id), None)
        location_name = zone.name if zone else event.zone_id

    text = (
        f"⏰ <b>Скоро закончится мероприятие!</b>\n\n"
        f"{emoji} <b>{event.name}</b>\n"
        f"📍 Место: {location_name}\n"
        f"⏰ Окончание: {time_str}\n\n"
        f"💡 Ожидается высокий спрос на такси!"
    )

    # Create route button - use venue coordinates if available, otherwise zone coordinates
    keyboard = None
    lat, lon = event.venue_lat, event.venue_lon

    if not lat or not lon:
        # Fall back to zone coordinates
        zones = get_zones()
        zone = next((z for z in zones if z.id == event.zone_id), None)
        if zone:
            lat, lon = zone.lat, zone.lon

    if lat and lon:
        from bot.handlers.route_chooser import make_route_callback
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Поехать", callback_data=make_route_callback(lat, lon, "menu"))],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
        ])

    # Send only to paid subscribers (Pro/Premium/Elite)
    await send_to_users_by_event_type(bot, text, event.event_type, keyboard, paid_only=True)
    logger.info("Sent pre-notification for event: %s (type: %s, venue: %s) to paid users only",
                event.name, event.event_type, event.venue_name or "unknown")


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

    # Use venue name if available, otherwise fall back to zone name
    location_name = event.venue_name
    if not location_name:
        zones = get_zones()
        zone = next((z for z in zones if z.id == event.zone_id), None)
        location_name = zone.name if zone else event.zone_id

    coeff_emoji = "🔥" if max_coeff >= 2.0 else "📈" if max_coeff >= 1.5 else "📊"

    text = (
        f"🎉 <b>Мероприятие закончилось!</b>\n\n"
        f"{emoji} <b>{event.name}</b>\n"
        f"📍 Место: {location_name}\n"
        f"{coeff_emoji} Коэффициент: <b>x{max_coeff:.2f}</b>\n\n"
        f"💰 Самое время работать в этой зоне!"
    )

    # Create route button - use venue coordinates if available, otherwise zone coordinates
    keyboard = None
    lat, lon = event.venue_lat, event.venue_lon

    if not lat or not lon:
        # Fall back to zone coordinates
        zones = get_zones()
        zone = next((z for z in zones if z.id == event.zone_id), None)
        if zone:
            lat, lon = zone.lat, zone.lon

    if lat and lon:
        from bot.handlers.route_chooser import make_route_callback
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚕 Поехать", callback_data=make_route_callback(lat, lon, "menu"))],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
        ])

    await send_to_users_by_event_type(bot, text, event.event_type, keyboard, paid_only=False)
    logger.info("Sent end notification for event: %s (type: %s, venue: %s, coeff: %.2f) to all users",
                event.name, event.event_type, event.venue_name or "unknown", max_coeff)


async def send_to_users_by_event_type(bot: Bot, text: str, event_type: str, keyboard: InlineKeyboardMarkup = None, paid_only: bool = False):
    """Send message to users who have notifications enabled for this event type.

    Args:
        bot: Bot instance
        text: Message text
        event_type: Event type to filter users
        keyboard: Inline keyboard
        paid_only: If True, send only to Pro/Premium/Elite users (for pre-notifications)
    """
    from bot.services.subscription import get_subscription

    async with session_factory() as session:
        stmt = select(User).where(User.event_notify_enabled == True)
        result = await session.execute(stmt)
        users = result.scalars().all()

        sent_count = 0
        skipped_quiet = 0
        skipped_free = 0

        for user in users:
            # Check quiet hours
            if is_quiet_hours(user):
                skipped_quiet += 1
                continue

            # Check if user wants notifications for this event type
            user_event_types = [t.strip() for t in user.event_types.split(",") if t.strip()]

            if event_type not in user_event_types:
                continue

            # Check subscription tier if paid_only is True
            if paid_only:
                subscription = await get_subscription(user.telegram_id)
                if subscription.tier == "free":
                    skipped_free += 1
                    continue

            # Use provided keyboard or create default one
            if not keyboard:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
                ])

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="HTML", reply_markup=keyboard)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to send notification to user %d: %s", user.telegram_id, e)

        if paid_only:
            logger.info("Sent event notification to %d paid users (event type: %s, skipped %d free, %d in quiet hours)",
                       sent_count, event_type, skipped_free, skipped_quiet)
        else:
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

            # Add main menu button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
            ])

            try:
                await bot.send_message(user.telegram_id, text, parse_mode="HTML", reply_markup=keyboard)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to send notification to user %d: %s", user.telegram_id, e)

        logger.info("Sent notification to %d users (skipped %d in quiet hours)", sent_count, skipped_quiet)
