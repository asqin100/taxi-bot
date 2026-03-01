"""Subscription renewal service - automatic subscription renewal."""
import logging
from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select, and_

from bot.database.db import get_session
from bot.models.subscription import Subscription, SubscriptionTier
from bot.services.payment import create_payment

logger = logging.getLogger(__name__)


async def get_expiring_subscriptions(days_before: int = 3) -> List[Subscription]:
    """
    Get subscriptions that will expire soon and have auto_renew enabled.

    Args:
        days_before: Number of days before expiration to check

    Returns:
        List of subscriptions to renew
    """
    async with get_session() as session:
        now = datetime.now()
        threshold = now + timedelta(days=days_before)

        result = await session.execute(
            select(Subscription).where(
                and_(
                    Subscription.auto_renew == True,
                    Subscription.is_active == True,
                    Subscription.expires_at != None,
                    Subscription.expires_at <= threshold,
                    Subscription.expires_at > now,
                    Subscription.tier != SubscriptionTier.FREE.value
                )
            )
        )
        subscriptions = result.scalars().all()
        return list(subscriptions)


async def process_subscription_renewals():
    """
    Process automatic subscription renewals.

    This function should be called periodically (e.g., daily) to check
    for subscriptions that need renewal.
    """
    try:
        subscriptions = await get_expiring_subscriptions(days_before=3)

        if not subscriptions:
            logger.info("No subscriptions to renew")
            return

        logger.info(f"Found {len(subscriptions)} subscriptions to renew")

        for subscription in subscriptions:
            try:
                tier = SubscriptionTier(subscription.tier)
                user_id = subscription.user_id

                # Create renewal payment
                payment_info = await create_payment(
                    user_id=user_id,
                    tier=tier,
                    duration_days=30
                )

                if payment_info:
                    logger.info(
                        f"Created renewal payment {payment_info['payment_id']} "
                        f"for user {user_id}, tier {tier.value}"
                    )
                    # TODO: Send notification to user about renewal payment
                else:
                    logger.warning(
                        f"Failed to create renewal payment for user {user_id}"
                    )

            except Exception as e:
                logger.error(
                    f"Error processing renewal for subscription {subscription.id}: {e}"
                )

    except Exception as e:
        logger.error(f"Error in subscription renewal process: {e}")


async def toggle_auto_renew(user_id: int, enabled: bool) -> bool:
    """
    Enable or disable auto-renewal for user's subscription.

    Args:
        user_id: User ID
        enabled: True to enable, False to disable

    Returns:
        True if successful
    """
    try:
        async with get_session() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            subscription = result.scalar_one_or_none()

            if not subscription:
                logger.warning(f"No subscription found for user {user_id}")
                return False

            subscription.auto_renew = enabled
            await session.commit()

            logger.info(
                f"Auto-renew {'enabled' if enabled else 'disabled'} "
                f"for user {user_id}"
            )
            return True

    except Exception as e:
        logger.error(f"Error toggling auto-renew for user {user_id}: {e}")
        return False
