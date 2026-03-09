import asyncio
import logging

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.models.subscription import SubscriptionTier
from bot.services.yandex_api import SurgeData, get_cached_coefficients
from bot.services.zones import get_zone_names_map
from bot.services.notification_utils import is_quiet_hours
from bot.services.subscription import get_subscription

logger = logging.getLogger(__name__)

TARIFF_LABELS = {"econom": "Эконом", "comfort": "Комфорт", "business": "Бизнес"}


async def check_and_notify(bot: Bot):
    """Check surge data against user thresholds and send notifications with priority delays."""
    zone_names = get_zone_names_map()
    all_data = get_cached_coefficients()
    if not all_data:
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.notify_enabled == True)  # noqa: E712
        )
        users = result.scalars().all()

    # Group users by subscription tier for priority notifications
    users_by_tier = {
        SubscriptionTier.ELITE: [],
        SubscriptionTier.PREMIUM: [],
        SubscriptionTier.PRO: [],
        SubscriptionTier.FREE: []
    }

    for user in users:
        # Check quiet hours
        if is_quiet_hours(user):
            continue

        subscription = await get_subscription(user.telegram_id)
        users_by_tier[subscription.tier].append(user)

    # Priority delays (cumulative)
    tier_delays = {
        SubscriptionTier.ELITE: 0,      # Immediate
        SubscriptionTier.PREMIUM: 60,   # 60 seconds after Elite
        SubscriptionTier.PRO: 90,       # 90 seconds after Elite
        SubscriptionTier.FREE: 120      # 120 seconds after Elite
    }

    total_sent = 0
    total_skipped_quiet = len(users) - sum(len(u) for u in users_by_tier.values())

    # Send notifications with priority delays
    for tier in [SubscriptionTier.ELITE, SubscriptionTier.PREMIUM, SubscriptionTier.PRO, SubscriptionTier.FREE]:
        tier_users = users_by_tier[tier]
        if not tier_users:
            continue

        # Wait for tier delay (except Elite which is immediate)
        if tier != SubscriptionTier.ELITE:
            delay = tier_delays[tier] - tier_delays.get(
                SubscriptionTier.ELITE if tier == SubscriptionTier.PREMIUM else
                SubscriptionTier.PREMIUM if tier == SubscriptionTier.PRO else
                SubscriptionTier.PRO,
                0
            )
            await asyncio.sleep(delay)

        sent_count = await _send_notifications_to_users(bot, tier_users, all_data, zone_names)
        total_sent += sent_count

        if sent_count > 0:
            logger.info("Sent %d notifications to %s users (delay: %ds)",
                       sent_count, tier.value.upper(), tier_delays[tier])

    if total_sent > 0 or total_skipped_quiet > 0:
        logger.info("Total: sent %d alerts, skipped %d in quiet hours", total_sent, total_skipped_quiet)


async def _send_notifications_to_users(bot: Bot, users: list[User], all_data: list[SurgeData], zone_names: dict) -> int:
    """Send notifications to a list of users."""
    sent_count = 0

    for user in users:
        user_tariffs = set(user.tariffs.split(",")) if user.tariffs else {"econom"}

        # Filter out business tariff for free users
        from bot.services.subscription import check_feature_access
        has_business = await check_feature_access(user.telegram_id, "business_tariff")

        if not has_business and "business" in user_tariffs:
            user_tariffs = {t for t in user_tariffs if t != "business"}

        # If no tariffs left after filtering, skip
        if not user_tariffs:
            continue

        user_zones = set(user.zones.split(",")) if user.zones else set()

        alerts: list[str] = []
        for sd in all_data:
            if sd.coefficient < user.surge_threshold:
                continue
            if sd.tariff not in user_tariffs:
                continue
            if user_zones and sd.zone_id not in user_zones:
                continue
            zone_name = zone_names.get(sd.zone_id, sd.zone_id)
            tariff_label = TARIFF_LABELS.get(sd.tariff, sd.tariff)
            alerts.append(f"  {zone_name} — {tariff_label}: x{sd.coefficient}")

        if alerts:
            text = "🔔 Высокие коэффициенты!\n\n" + "\n".join(alerts)

            # Add main menu button
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
            ])

            try:
                await bot.send_message(user.telegram_id, text, reply_markup=keyboard)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to notify user %s: %s", user.telegram_id, e)

    return sent_count
