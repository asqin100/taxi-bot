"""Nightclub alert service - sends alerts about high demand near nightclubs."""
import json
import logging
from datetime import datetime, time
from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.database.db import session_factory
from bot.models.user import User
from bot.services.notification_utils import is_quiet_hours
from bot.utils.timezone import now as get_moscow_now
from sqlalchemy import select

logger = logging.getLogger(__name__)

NIGHTCLUBS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "nightclubs.json"


class NightclubManager:
    """Manages nightclub data and alerts."""

    def __init__(self):
        self.nightclubs = []
        self._load_nightclubs()

    def _load_nightclubs(self):
        """Load nightclub data from JSON."""
        try:
            with open(NIGHTCLUBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.nightclubs = data.get("nightclubs", [])
            logger.info("Loaded %d nightclubs", len(self.nightclubs))
        except Exception as e:
            logger.error("Failed to load nightclubs: %s", e)
            self.nightclubs = []

    def get_nightclubs_for_alert(self) -> list[dict]:
        """Get nightclubs that should send alerts now.

        Returns nightclubs if:
        - Current day is Friday (4) or Saturday (5)
        - Current time is around 05:00 (between 04:50 and 05:10)
        """
        now = get_moscow_now()
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday
        current_time = now.time()

        # Check if it's Friday or Saturday
        if current_weekday not in [4, 5]:  # Friday or Saturday
            return []

        # Check if time is around 05:00 (04:50 - 05:10)
        alert_start = time(4, 50)
        alert_end = time(5, 10)

        if not (alert_start <= current_time <= alert_end):
            return []

        # Return all nightclubs (they all have same schedule)
        return self.nightclubs


nightclub_manager = NightclubManager()


async def check_and_send_nightclub_alerts(bot: Bot):
    """Check if it's time to send nightclub alerts and send them."""
    logger.info("Checking for nightclub alerts...")

    nightclubs = nightclub_manager.get_nightclubs_for_alert()

    if not nightclubs:
        logger.debug("No nightclub alerts to send at this time")
        return

    logger.info("Sending nightclub alerts for %d clubs", len(nightclubs))

    # Send alerts to all users with nightclub alerts enabled
    async with session_factory() as session:
        stmt = select(User).where(User.nightclub_alerts_enabled == True)
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
                # Send alert for each nightclub
                for club in nightclubs:
                    text = (
                        f"🌃 <b>Ночные клубы закрываются!</b>\n\n"
                        f"🎉 <b>{club['name']}</b>\n"
                        f"📍 {club['address']}\n\n"
                        f"💰 Сейчас высокий спрос на такси возле ночных клубов!\n"
                        f"⏰ Самое время подъехать к этой локации."
                    )

                    # Create route button
                    from bot.handlers.route_chooser import make_route_callback
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🚕 Поехать", callback_data=make_route_callback(club['lat'], club['lon'], "menu"))],
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
                    ])

                    await bot.send_message(user.telegram_id, text, parse_mode="HTML", reply_markup=keyboard)
                    sent_count += 1

            except Exception as e:
                logger.warning("Failed to send nightclub alert to user %d: %s", user.telegram_id, e)

        logger.info("Sent nightclub alerts to %d users (skipped %d in quiet hours)", sent_count, skipped_quiet)
