import logging

from aiogram import Bot
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.services.yandex_api import SurgeData, get_cached_coefficients
from bot.services.zones import get_zone_names_map
from bot.services.notification_utils import is_quiet_hours

logger = logging.getLogger(__name__)

TARIFF_LABELS = {"econom": "Эконом", "comfort": "Комфорт", "business": "Бизнес"}


async def check_and_notify(bot: Bot):
    """Check surge data against user thresholds and send notifications."""
    zone_names = get_zone_names_map()
    all_data = get_cached_coefficients()
    if not all_data:
        return

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.notify_enabled == True)  # noqa: E712
        )
        users = result.scalars().all()

    sent_count = 0
    skipped_quiet = 0

    for user in users:
        # Check quiet hours
        if is_quiet_hours(user):
            skipped_quiet += 1
            continue

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
            try:
                await bot.send_message(user.telegram_id, text)
                sent_count += 1
            except Exception as e:
                logger.warning("Failed to notify user %s: %s", user.telegram_id, e)

    if sent_count > 0 or skipped_quiet > 0:
        logger.info("Sent coefficient alerts to %d users (skipped %d in quiet hours)", sent_count, skipped_quiet)
