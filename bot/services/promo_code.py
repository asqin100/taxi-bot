"""Promo code service - validate and activate promo codes."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import get_session
from bot.models.promo_code import PromoCode, PromoCodeUsage
from bot.models.subscription import SubscriptionTier
from bot.models.user import User
from bot.services.subscription import upgrade_subscription

logger = logging.getLogger(__name__)


async def ensure_user_exists(user_id: int, username: Optional[str] = None) -> None:
    """Ensure user record exists in database, create if missing."""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            # Generate referral code for new user
            from bot.services.referral import generate_referral_code

            while True:
                code = generate_referral_code()
                existing = await session.execute(
                    select(User).where(User.referral_code == code)
                )
                if not existing.scalar_one_or_none():
                    break

            user = User(
                telegram_id=user_id,
                username=username,
                referral_code=code,
                created_at=datetime.now(),
            )
            session.add(user)
            await session.commit()
            logger.info(f"Created user record for {user_id} during promo activation")


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


async def activate_promo_code(code: str, user_id: int, tier: Optional[str] = None, username: Optional[str] = None) -> tuple[bool, str, Optional[PromoCode]]:
    """
    Activate promo code for user.

    Args:
        code: Promo code
        user_id: User ID
        tier: Target tier (required for discount type)
        username: Username (optional, for creating user record if needed)

    Returns:
        (success, message, promo_code_object)
    """
    # Validate first
    is_valid, error_msg, promo = await validate_promo_code(code, user_id)
    if not is_valid:
        return False, error_msg, None

    tier_names = {
        "pro": "⭐ Pro",
        "premium": "💎 Premium",
        "elite": "👑 Elite"
    }

    if promo.promo_type == "activation":
        # Ensure user exists before creating subscription
        await ensure_user_exists(user_id, username)

        # Free subscription activation
        async with get_session() as session:
            promo.current_uses += 1
            session.add(promo)

            usage = PromoCodeUsage(
                promo_code_id=promo.id,
                user_id=user_id,
                promo_type="activation",
                tier=promo.tier,
                duration_days=promo.duration_days
            )
            session.add(usage)
            await session.commit()

        # Upgrade subscription
        tier_obj = SubscriptionTier(promo.tier)
        await upgrade_subscription(
            user_id=user_id,
            tier=tier_obj,
            duration_days=promo.duration_days,
            payment_method="promo_code"
        )

        tier_name = tier_names.get(promo.tier, promo.tier)
        logger.info("User %d activated promo code %s (%s, %d days)",
                    user_id, code, promo.tier, promo.duration_days)

        return True, (
            f"✅ <b>Промокод активирован!</b>\n\n"
            f"🎉 Вам предоставлена подписка <b>{tier_name}</b> на {promo.duration_days} дней\n\n"
            f"Наслаждайтесь всеми возможностями!"
        ), promo

    elif promo.promo_type == "discount":
        # Discount code - return info for user to choose tier
        if not tier:
            # Show available tiers
            applicable = promo.get_applicable_tiers()
            tiers_text = ", ".join([tier_names.get(t, t) for t in applicable])

            discount_text = ""
            if promo.discount_type == "percent":
                discount_text = f"{int(promo.discount_value)}%"
            else:
                discount_text = f"{int(promo.discount_value)}₽"

            return True, (
                f"🎁 <b>Промокод на скидку!</b>\n\n"
                f"💰 Скидка: <b>{discount_text}</b>\n"
                f"📋 Применяется к тарифам: {tiers_text}\n\n"
                f"Выберите тариф для оплаты со скидкой:"
            ), promo

        # Apply discount to specific tier
        if not promo.is_applicable_to_tier(tier):
            return False, f"❌ Промокод не применим к тарифу {tier_names.get(tier, tier)}", None

        # Return promo for payment processing
        return True, "discount_ready", promo

    return False, "❌ Неизвестный тип промокода", None


async def create_promo_code(
    code: str,
    promo_type: str = "activation",
    tier: Optional[str] = None,
    duration_days: Optional[int] = None,
    discount_type: Optional[str] = None,
    discount_value: Optional[float] = None,
    applicable_tiers: Optional[list[str]] = None,
    max_uses: Optional[int] = None,
    valid_until: Optional[datetime] = None,
    description: Optional[str] = None,
    created_by: Optional[int] = None
) -> PromoCode:
    """Create new promo code (activation or discount)."""
    async with get_session() as session:
        promo = PromoCode(
            code=code.upper(),
            promo_type=promo_type,
            tier=tier,
            duration_days=duration_days,
            discount_type=discount_type,
            discount_value=discount_value,
            applicable_tiers=",".join(applicable_tiers) if applicable_tiers else None,
            max_uses=max_uses,
            valid_until=valid_until,
            description=description,
            created_by=created_by
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)

        if promo_type == "activation":
            logger.info("Created activation promo code %s (%s, %d days, max_uses=%s)",
                       code, tier, duration_days, max_uses)
        else:
            logger.info("Created discount promo code %s (%s %s, tiers=%s, max_uses=%s)",
                       code, discount_value, discount_type, applicable_tiers, max_uses)

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


async def record_discount_usage(
    promo_code_id: int,
    user_id: int,
    tier: str,
    original_price: float,
    discount_amount: float,
    final_price: float
) -> None:
    """Record discount promo code usage."""
    async with get_session() as session:
        # Increment usage counter
        result = await session.execute(
            select(PromoCode).where(PromoCode.id == promo_code_id)
        )
        promo = result.scalar_one_or_none()
        if promo:
            promo.current_uses += 1
            session.add(promo)

        # Record usage
        usage = PromoCodeUsage(
            promo_code_id=promo_code_id,
            user_id=user_id,
            promo_type="discount",
            tier=tier,
            original_price=original_price,
            discount_amount=discount_amount,
            final_price=final_price
        )
        session.add(usage)
        await session.commit()

        logger.info("User %d used discount promo (code_id=%d, tier=%s, discount=%.2f)",
                   user_id, promo_code_id, tier, discount_amount)
