import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import settings
from bot.database.db import init_db
from bot.handlers import start, coefficients, settings as settings_handler, notifications, events, search, financial, traffic, menu, hotspots, subscription, ai_advisor, achievements, challenges, leaderboard, help as help_handler, onboarding, referral, location, export, statistics, tax, heatmap, subscription_check
from bot.middlewares.auth import ThrottleMiddleware
from bot.middlewares.channel_subscription import ChannelSubscriptionMiddleware
from bot.services.yandex_api import fetch_all_coefficients
from bot.services.coefficient_collector import collect_and_store_coefficients
from bot.services.notifier import check_and_notify
from bot.services.event_notifier import check_and_notify_events
from bot.services.event_parser import fetch_and_store_events
from bot.services.payment import init_yookassa
from bot.services.subscription_renewal import process_subscription_renewals
from bot.services.geo_alerts import check_geo_alerts
from bot.services.live_location_reminder import check_live_location_expiration
from bot.web.api import create_app

# Import models to ensure they're registered with SQLAlchemy
from bot.models.user import User
from bot.models.shift import Shift
from bot.models.subscription import Subscription
from bot.models.financial_settings import UserFinancialSettings
from bot.models.achievement import UserAchievement
from bot.models.challenge import UserChallenge
from bot.models.ai_usage import AIUsage
from bot.models.referral import ReferralEarning

from aiohttp import web

# Configure logging with both console and file handlers
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


async def _initial_fetch():
    """Fetch initial data in background without blocking bot startup."""
    try:
        logger.info("Starting initial coefficient fetch...")
        await fetch_all_coefficients()
        logger.info("Initial coefficient fetch complete")
    except Exception as e:
        logger.error("Initial coefficient fetch failed: %s", e)

    try:
        logger.info("Starting initial event parsing...")
        await fetch_and_store_events()
        logger.info("Initial event parsing complete")
    except Exception as e:
        logger.warning("Initial event parsing failed: %s", e)


async def main():
    await init_db()
    logger.info("Database initialized")

    # Initialize payment system
    init_yookassa()

    bot = Bot(token=settings.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Middleware
    dp.message.middleware(ThrottleMiddleware(rate_limit=0.5))
    dp.message.middleware(ChannelSubscriptionMiddleware())
    dp.callback_query.middleware(ChannelSubscriptionMiddleware())

    # Routers
    dp.include_router(subscription_check.router)  # Must be first to handle subscription check
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(onboarding.router)
    dp.include_router(coefficients.router)
    dp.include_router(settings_handler.router)
    dp.include_router(notifications.router)
    dp.include_router(location.router)
    dp.include_router(events.router)
    dp.include_router(search.router)
    dp.include_router(financial.router)
    dp.include_router(traffic.router)
    dp.include_router(hotspots.router)
    dp.include_router(subscription.router)
    dp.include_router(referral.router)
    dp.include_router(ai_advisor.router)
    dp.include_router(achievements.router)
    dp.include_router(challenges.router)
    dp.include_router(leaderboard.router)
    dp.include_router(help_handler.router)
    dp.include_router(export.router)
    dp.include_router(statistics.router)
    dp.include_router(tax.router)
    dp.include_router(heatmap.router)

    # Initial fetch in background (non-blocking)
    asyncio.create_task(_initial_fetch())
    logger.info("Initial data fetch scheduled in background")

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_all_coefficients, "interval", seconds=settings.parse_interval_seconds)
    scheduler.add_job(collect_and_store_coefficients, "interval", seconds=settings.parse_interval_seconds + 10)  # Store coefficients 10s after fetch
    scheduler.add_job(check_and_notify, "interval", seconds=settings.parse_interval_seconds + 5, args=[bot])
    scheduler.add_job(check_geo_alerts, "interval", seconds=120, args=[bot])  # Check geo alerts every 2 minutes
    scheduler.add_job(check_live_location_expiration, "interval", seconds=300, args=[bot])  # Check expiration every 5 minutes
    scheduler.add_job(check_and_notify_events, "interval", seconds=60, args=[bot])  # Check events every minute
    scheduler.add_job(fetch_and_store_events, "interval", hours=6)  # Parse events every 6 hours
    scheduler.add_job(process_subscription_renewals, "interval", hours=24)  # Check renewals daily
    scheduler.start()
    logger.info("Scheduler started (interval=%ds)", settings.parse_interval_seconds)

    # Web server
    webapp = create_app()
    webapp["bot"] = bot  # Store bot instance for admin broadcast
    runner = web.AppRunner(webapp)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", settings.web_port)
    await site.start()
    logger.info("Web server started on port %d", settings.web_port)

    try:
        logger.info("Bot starting polling...")
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
