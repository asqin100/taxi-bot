"""AI Usage service - track and limit AI advisor usage."""
import logging
from datetime import datetime, date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from bot.database.db import get_session
from bot.models.ai_usage import AIUsage
from bot.services.subscription import get_user_subscription

logger = logging.getLogger(__name__)

# Daily limits by subscription tier
AI_LIMITS = {
    "free": 0,      # AI advisor not available for free tier
    "pro": 5,       # 5 questions per day
    "premium": 20   # 20 questions per day
}


async def get_daily_usage(user_id: int, usage_date: Optional[date] = None) -> int:
    """
    Get user's AI usage count for a specific date.

    Args:
        user_id: User's telegram ID
        usage_date: Date to check (defaults to today)

    Returns:
        Number of questions asked today
    """
    if usage_date is None:
        usage_date = datetime.now().date()

    async with get_session() as session:
        result = await session.execute(
            select(AIUsage).where(
                AIUsage.user_id == user_id,
                AIUsage.date == usage_date
            )
        )
        usage = result.scalar_one_or_none()

        return usage.question_count if usage else 0


async def get_daily_limit(user_id: int) -> int:
    """
    Get user's daily AI question limit based on subscription tier.

    Args:
        user_id: User's telegram ID

    Returns:
        Daily question limit
    """
    subscription = await get_user_subscription(user_id)

    if not subscription:
        return AI_LIMITS["free"]

    tier = subscription.tier
    return AI_LIMITS.get(tier, AI_LIMITS["free"])


async def check_can_ask(user_id: int) -> tuple[bool, int, int]:
    """
    Check if user can ask another AI question today.

    Args:
        user_id: User's telegram ID

    Returns:
        Tuple of (can_ask, current_usage, daily_limit)
    """
    current_usage = await get_daily_usage(user_id)
    daily_limit = await get_daily_limit(user_id)

    can_ask = current_usage < daily_limit

    return can_ask, current_usage, daily_limit


async def increment_usage(user_id: int) -> bool:
    """
    Increment user's AI usage count for today.

    Args:
        user_id: User's telegram ID

    Returns:
        True if incremented successfully, False otherwise
    """
    today = datetime.now().date()

    async with get_session() as session:
        # Try to get existing usage record
        result = await session.execute(
            select(AIUsage).where(
                AIUsage.user_id == user_id,
                AIUsage.date == today
            )
        )
        usage = result.scalar_one_or_none()

        if usage:
            # Update existing record
            usage.question_count += 1
        else:
            # Create new record
            usage = AIUsage(
                user_id=user_id,
                date=today,
                question_count=1
            )
            session.add(usage)

        try:
            await session.commit()
            logger.info(f"Incremented AI usage for user {user_id}: {usage.question_count}")
            return True
        except IntegrityError as e:
            logger.error(f"Failed to increment AI usage: {e}")
            await session.rollback()
            return False


async def get_usage_stats(user_id: int) -> dict:
    """
    Get user's AI usage statistics.

    Args:
        user_id: User's telegram ID

    Returns:
        Dictionary with usage stats
    """
    current_usage = await get_daily_usage(user_id)
    daily_limit = await get_daily_limit(user_id)
    remaining = max(0, daily_limit - current_usage)

    return {
        "used": current_usage,
        "limit": daily_limit,
        "remaining": remaining,
        "can_ask": remaining > 0
    }
