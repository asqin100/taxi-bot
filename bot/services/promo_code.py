"""Promo code service - validate and activate promo codes."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import get_session
from bot.models.promo_code import PromoCode, PromoCodeUsage
from bot.models.subscription import SubscriptionTier
from bot.services.subscription import upgrade_subscription

logger = logging.getLogger(__name__)


async def validate_promo_code(code: str, user_id: int) -> tuple[bool, str, Optional[PromoCode]]:
    """
    Validate promo code for user.

    Returns:
        (is_valid, error_message, promo_code_object)
    """
    async with get_session() as session:
        # Find promo code
        result = await session.execute(
            select(PromoCode).where(PromoCode.code == code.upper())
        )
        promo = result.scalar_one_or_none()

        if not promo:
            return False, "❌ Промокод не найден", None

        # Check if valid
        if not promo.is_valid:
            if not promo.is_active:
                return False, "❌ Промокод деактивирован", None

            now = datetime.now()
            if now < promo.valid_from:
                return False, "❌ Промокод ещё не активен", None

            if promo.valid_until and now > promo.valid_until:
                return False, "❌ Промокод истёк", None

            if promo.max_uses is not None and promo.current_uses >= promo.max_uses:
                return False, "❌ Промокод исчерпан", None

        # Check if user already used this promo
        usage_result = await session.execute(
            select(PromoCodeUsage).where(
                PromoCodeUsage.promo_code_id == promo.id,
                PromoCodeUsage.user_id == user_id
            )
        )
        if usage_result.scalar_one_or_none():
            return False, "❌ Вы уже использовали этот промокод", None

        return True, "", promo


async def activate_promo_code(code: str, user_id: int) -> tuple[bool, str]:
    """
    Activate promo code for user.

    Returns:
        (success, message)
    """
    # Validate first
    is_valid, error_msg, promo = await validate_promo_code(code, user_id)
    if not is_valid:
        return False, error_msg

    async with get_session() as session:
        # Increment usage counter
        promo.current_uses += 1
        session.add(promo)

        # Record usage
        usage = PromoCodeUsage(
            promo_code_id=promo.id,
            user_id=user_id,
            tier=promo.tier,
            duration_days=promo.duration_days
        )
        session.add(usage)

        await session.commit()

    # Upgrade subscription
    tier = SubscriptionTier(promo.tier)
    await upgrade_subscription(
        user_id=user_id,
        tier=tier,
        duration_days=promo.duration_days,
        payment_method="promo_code"
    )

    tier_names = {
        "pro": "Pro",
        "premium": "Premium",
        "elite": "Elite"
    }
    tier_name = tier_names.get(promo.tier, promo.tier)

    logger.info("User %d activated promo code %s (%s, %d days)",
                user_id, code, promo.tier, promo.duration_days)

    return True, (
        f"✅ <b>Промокод активирован!</b>\n\n"
        f"🎉 Вам предоставлена подписка <b>{tier_name}</b> на {promo.duration_days} дней\n\n"
        f"Наслаждайтесь всеми возможностями!"
    )


async def create_promo_code(
    code: str,
    tier: str,
    duration_days: int,
    max_uses: Optional[int] = None,
    valid_until: Optional[datetime] = None,
    description: Optional[str] = None,
    created_by: Optional[int] = None
) -> PromoCode:
    """Create new promo code."""
    async with get_session() as session:
        promo = PromoCode(
            code=code.upper(),
            tier=tier,
            duration_days=duration_days,
            max_uses=max_uses,
            valid_until=valid_until,
            description=description,
            created_by=created_by
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)

        logger.info("Created promo code %s (%s, %d days, max_uses=%s)",
                   code, tier, duration_days, max_uses)

        return promo


async def get_all_promo_codes() -> list[PromoCode]:
    """Get all promo codes for admin panel."""
    async with get_session() as session:
        result = await session.execute(
            select(PromoCode).order_by(PromoCode.created_at.desc())
        )
        return list(result.scalars().all())


async def deactivate_promo_code(code: str) -> bool:
    """Deactivate promo code."""
    async with get_session() as session:
        result = await session.execute(
            select(PromoCode).where(PromoCode.code == code.upper())
        )
        promo = result.scalar_one_or_none()

        if not promo:
            return False

        promo.is_active = False
        await session.commit()

        logger.info("Deactivated promo code %s", code)
        return True
