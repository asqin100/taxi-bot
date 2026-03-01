"""Subscription service - manage user subscriptions and limits."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import get_session
from bot.models.subscription import Subscription, SubscriptionTier, SUBSCRIPTION_FEATURES

logger = logging.getLogger(__name__)


async def get_subscription(user_id: int) -> Subscription:
    """Get user subscription, create if doesn't exist."""
    async with get_session() as session:
        result = await session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            # Create free subscription for new user
            subscription = Subscription(
                user_id=user_id,
                tier=SubscriptionTier.FREE.value,
                is_active=True
            )
            session.add(subscription)
            await session.commit()
            await session.refresh(subscription)
            logger.info("Created free subscription for user %d", user_id)

        return subscription


# Alias for compatibility
get_user_subscription = get_subscription


async def upgrade_subscription(
    user_id: int,
    tier: SubscriptionTier,
    duration_days: int = 30,
    payment_method: str = "manual"
) -> Subscription:
    """Upgrade user subscription to a higher tier."""
    async with get_session() as session:
        result = await session.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            subscription = Subscription(user_id=user_id)
            session.add(subscription)

        subscription.tier = tier.value
        subscription.is_active = True
        subscription.started_at = datetime.now()
        subscription.expires_at = datetime.now() + timedelta(days=duration_days)
        subscription.last_payment_at = datetime.now()
        subscription.payment_method = payment_method

        await session.commit()
        await session.refresh(subscription)

        logger.info("Upgraded user %d to %s tier", user_id, tier.value)
        return subscription


async def check_feature_access(user_id: int, feature: str) -> bool:
    """Check if user has access to a specific feature."""
    subscription = await get_subscription(user_id)

    # Check if subscription is expired
    if subscription.is_expired:
        return False

    features = SUBSCRIPTION_FEATURES.get(SubscriptionTier(subscription.tier), {})
    return features.get(feature, False)


async def get_alert_limit(user_id: int) -> int:
    """Get maximum number of alerts for user's subscription tier."""
    subscription = await get_subscription(user_id)
    features = SUBSCRIPTION_FEATURES.get(SubscriptionTier(subscription.tier), {})
    return features.get("max_alerts", 3)


async def can_create_alert(user_id: int, current_alert_count: int) -> bool:
    """Check if user can create more alerts."""
    limit = await get_alert_limit(user_id)
    return current_alert_count < limit


def format_subscription_info(subscription: Subscription) -> str:
    """Format subscription information as text."""
    tier = SubscriptionTier(subscription.tier)
    features = SUBSCRIPTION_FEATURES.get(tier, {})

    lines = []

    # Header
    if tier == SubscriptionTier.FREE:
        lines.append("🆓 <b>БЕСПЛАТНЫЙ ТАРИФ</b>\n")
    elif tier == SubscriptionTier.PRO:
        lines.append("⭐ <b>PRO ТАРИФ</b>\n")
    else:
        lines.append("💎 <b>PREMIUM ТАРИФ</b>\n")

    # Status
    if subscription.is_expired:
        lines.append("❌ <b>Статус:</b> Истёк")
        lines.append(f"📅 <b>Истёк:</b> {subscription.expires_at.strftime('%d.%m.%Y')}\n")
    elif subscription.expires_at:
        lines.append("✅ <b>Статус:</b> Активен")
        lines.append(f"📅 <b>Действует до:</b> {subscription.expires_at.strftime('%d.%m.%Y')}\n")
    else:
        lines.append("✅ <b>Статус:</b> Активен (бессрочно)\n")

    # Features
    lines.append("<b>Возможности:</b>")
    for feature in features.get("features", []):
        lines.append(f"  {feature}")

    return "\n".join(lines)


def format_tier_comparison() -> str:
    """Format comparison of all subscription tiers."""
    lines = ["<b>📊 СРАВНЕНИЕ ТАРИФОВ</b>\n"]

    for tier in [SubscriptionTier.FREE, SubscriptionTier.PRO, SubscriptionTier.PREMIUM]:
        features = SUBSCRIPTION_FEATURES[tier]
        price = features["price"]

        if tier == SubscriptionTier.FREE:
            lines.append("🆓 <b>Бесплатный</b> — 0₽/мес")
        elif tier == SubscriptionTier.PRO:
            lines.append(f"\n⭐ <b>Pro</b> — {price}₽/мес")
        else:
            lines.append(f"\n💎 <b>Premium</b> — {price}₽/мес")

        for feature in features["features"][:3]:  # Show first 3 features
            lines.append(f"  {feature}")

        if len(features["features"]) > 3:
            lines.append(f"  ... и ещё {len(features['features']) - 3}")

    return "\n".join(lines)
