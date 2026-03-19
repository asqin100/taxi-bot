"""Service for tracking 'Where to go' feature usage."""
import logging
from datetime import datetime, date
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.where_to_go_usage import WhereToGoUsage
from bot.services.subscription import get_subscription
from bot.models.subscription import SUBSCRIPTION_FEATURES

logger = logging.getLogger(__name__)


async def check_where_to_go_limit(user_id: int) -> tuple[bool, int, int]:
    """
    Check if user can use 'Where to go' feature.

    Returns:
        tuple: (can_use, current_usage, daily_limit)
    """
    logger.info(f"Checking 'Where to go' limit for user {user_id}")

    # Get user's subscription
    subscription = await get_subscription(user_id)
    tier_features = SUBSCRIPTION_FEATURES.get(subscription.tier, {})
    daily_limit = tier_features.get("where_to_go_limit", 3)

    logger.info(f"User {user_id} has tier '{subscription.tier}' with daily limit: {daily_limit}")

    # Get today's usage
    today = date.today()

    async with session_factory() as session:
        result = await session.execute(
            select(WhereToGoUsage).where(
                WhereToGoUsage.user_id == user_id,
                WhereToGoUsage.date == today
            )
        )
        usage_record = result.scalar_one_or_none()

        current_usage = usage_record.usage_count if usage_record else 0

        logger.info(f"User {user_id} current usage today: {current_usage}/{daily_limit}")

        can_use = current_usage < daily_limit

        if not can_use:
            logger.warning(f"User {user_id} exceeded 'Where to go' limit: {current_usage}/{daily_limit}")

        return can_use, current_usage, daily_limit


async def record_where_to_go_use(user_id: int) -> None:
    """
    Record a 'Where to go' feature usage.

    Args:
        user_id: Telegram user ID
    """
    logger.info(f"Recording 'Where to go' usage for user {user_id}")

    today = date.today()

    async with session_factory() as session:
        # Get or create usage record for today
        result = await session.execute(
            select(WhereToGoUsage).where(
                WhereToGoUsage.user_id == user_id,
                WhereToGoUsage.date == today
            )
        )
        usage_record = result.scalar_one_or_none()

        if usage_record:
            usage_record.usage_count += 1
            logger.info(f"Updated usage count for user {user_id}: {usage_record.usage_count}")
        else:
            usage_record = WhereToGoUsage(
                user_id=user_id,
                date=today,
                usage_count=1
            )
            session.add(usage_record)
            logger.info(f"Created new usage record for user {user_id}: count=1")

        await session.commit()
        logger.info(f"Successfully recorded 'Where to go' usage for user {user_id}")


async def get_where_to_go_usage(user_id: int) -> tuple[int, int]:
    """
    Get current usage and limit for user.

    Returns:
        tuple: (current_usage, daily_limit)
    """
    today = date.today()

    # Get subscription limit
    subscription = await get_subscription(user_id)
    tier_features = SUBSCRIPTION_FEATURES.get(subscription.tier, {})
    daily_limit = tier_features.get("where_to_go_limit", 3)

    # Get today's usage
    async with session_factory() as session:
        result = await session.execute(
            select(WhereToGoUsage).where(
                WhereToGoUsage.user_id == user_id,
                WhereToGoUsage.date == today
            )
        )
        usage_record = result.scalar_one_or_none()
        current_usage = usage_record.usage_count if usage_record else 0

    return current_usage, daily_limit
