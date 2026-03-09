"""Geolocation-based surge alerts for drivers."""

import logging
import math
from datetime import datetime, timedelta

from sqlalchemy import select
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.db import session_factory
from bot.models.user import User
from bot.services.yandex_api import get_cached_coefficients
from bot.services.zones import get_zones

logger = logging.getLogger(__name__)

# Alert cooldown: don't send same zone alert more than once per 15 minutes
ALERT_COOLDOWN_MINUTES = 15
# Distance threshold: alert if high surge zone is within 5 km
DISTANCE_THRESHOLD_KM = 5.0

# Track last alert time per user per zone
_last_alerts: dict[tuple[int, str], datetime] = {}


def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km using Haversine formula."""
    dlat = lat2 - lat1
    dlon = (lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
    return math.sqrt(dlat**2 + dlon**2) * 111.32


async def check_geo_alerts(bot: Bot):
    """Check all users with geo alerts enabled and send notifications if needed."""
    try:
        async with session_factory() as session:
            # Get users with geo alerts enabled and valid location
            result = await session.execute(
                select(User).where(
                    User.geo_alerts_enabled == True,
                    User.last_latitude.isnot(None),
                    User.last_longitude.isnot(None),
                )
            )
            users = result.scalars().all()

        if not users:
            return

        logger.info(f"Checking geo alerts for {len(users)} users")

        # Get current coefficients (from cache)
        zones = get_zones()
        zone_map = {z.id: z for z in zones}

        for user in users:
            try:
                await _check_user_alerts(bot, user, zone_map)
            except Exception as e:
                logger.error(f"Error checking alerts for user {user.telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Error in check_geo_alerts: {e}")


async def _check_user_alerts(bot: Bot, user: User, zone_map: dict):
    """Check alerts for a single user."""
    # Check if user has access to geo alerts feature
    from bot.services.subscription import check_feature_access, get_alert_limit, get_alert_cooldown

    has_access = await check_feature_access(user.telegram_id, "geo_alerts")
    if not has_access:
        return

    # Check daily limit
    from bot.database.db import session_factory
    async with session_factory() as session:
        # Refresh user object in this session
        from sqlalchemy import select
        from bot.models.user import User as UserModel
        result = await session.execute(
            select(UserModel).where(UserModel.telegram_id == user.telegram_id)
        )
        db_user = result.scalar_one()

        # Reset counter if it's a new day
        now = datetime.now()
        if db_user.geo_alerts_reset_date is None or db_user.geo_alerts_reset_date.date() < now.date():
            db_user.geo_alerts_sent_today = 0
            db_user.geo_alerts_reset_date = now
            await session.commit()
            logger.info(f"Reset geo alerts counter for user {user.telegram_id}")

        # Check if user has reached daily limit
        daily_limit = await get_alert_limit(user.telegram_id)
        if db_user.geo_alerts_sent_today >= daily_limit:
            logger.info(f"User {user.telegram_id} reached daily geo alerts limit ({daily_limit})")
            return

        # Calculate remaining alerts
        remaining_alerts = daily_limit - db_user.geo_alerts_sent_today

    user_lat = user.last_latitude
    user_lon = user.last_longitude
    threshold = user.surge_threshold

    # Get user's alert cooldown based on subscription tier
    user_cooldown_seconds = await get_alert_cooldown(user.telegram_id)

    # Get user's tariffs
    tariffs = user.tariffs.split(",") if user.tariffs else ["econom"]

    # Get cached coefficients for user's tariffs
    alerts_to_send = []

    for tariff in tariffs:
        data = get_cached_coefficients(tariff)

        for surge_data in data:
            if surge_data.coefficient < threshold:
                continue

            zone = zone_map.get(surge_data.zone_id)
            if not zone:
                continue

            # Calculate distance
            distance = _calculate_distance(user_lat, user_lon, zone.lat, zone.lon)

            if distance <= DISTANCE_THRESHOLD_KM:
                # Check cooldown based on user's subscription tier
                alert_key = (user.telegram_id, surge_data.zone_id)
                last_alert = _last_alerts.get(alert_key)
                now = datetime.now()

                if last_alert and user_cooldown_seconds > 0 and (now - last_alert).total_seconds() < user_cooldown_seconds:
                    continue

                # Add to alerts
                alerts_to_send.append({
                    "zone": zone,
                    "coefficient": surge_data.coefficient,
                    "tariff": surge_data.tariff,
                    "distance": distance,
                })

                # Update cooldown
                _last_alerts[alert_key] = now

    # Send alerts (limited by remaining daily limit)
    alerts_sent = 0
    for alert in alerts_to_send[:remaining_alerts]:
        await _send_alert(bot, user, alert)
        alerts_sent += 1

    # Update counter in database
    if alerts_sent > 0:
        async with session_factory() as session:
            result = await session.execute(
                select(UserModel).where(UserModel.telegram_id == user.telegram_id)
            )
            db_user = result.scalar_one()
            db_user.geo_alerts_sent_today += alerts_sent
            await session.commit()
            logger.info(f"Sent {alerts_sent} geo alerts to user {user.telegram_id}, total today: {db_user.geo_alerts_sent_today}/{daily_limit}")


async def _send_alert(bot: Bot, user: User, alert: dict):
    """Send a single geo alert to user."""
    zone = alert["zone"]
    coeff = alert["coefficient"]
    tariff = alert["tariff"]
    distance = alert["distance"]

    tariff_names = {
        "econom": "Эконом",
        "comfort": "Комфорт",
        "business": "Бизнес",
    }

    text = (
        f"🔥 <b>ВЫСОКИЙ КОЭФФИЦИЕНТ РЯДОМ!</b>\n\n"
        f"📍 Зона: <b>{zone.name}</b>\n"
        f"💰 Коэффициент: <b>x{coeff}</b>\n"
        f"🚗 Тариф: {tariff_names.get(tariff, tariff)}\n"
        f"📏 Расстояние: <b>{distance:.1f} км</b>\n\n"
        f"Выберите приложение для навигации:"
    )

    # Yandex Maps and Navigator URLs
    maps_url = f"https://yandex.ru/maps/?rtext=~{zone.lat},{zone.lon}&rtt=auto"
    navigator_url = f"yandexnavi://build_route_on_map?lat_to={zone.lat}&lon_to={zone.lon}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗺 Яндекс.Карты", url=maps_url),
            InlineKeyboardButton(text="🧭 Яндекс.Навигатор", url=navigator_url),
        ],
        [InlineKeyboardButton(text="🔕 Отключить геоалерты", callback_data="geo_alerts:disable")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    try:
        await bot.send_message(
            chat_id=user.telegram_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        logger.info(f"Sent geo alert to user {user.telegram_id}: {zone.name} x{coeff}")
    except Exception as e:
        logger.error(f"Failed to send geo alert to {user.telegram_id}: {e}")
