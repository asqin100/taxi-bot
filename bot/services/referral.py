"""Referral service - 2-level referral system with balance."""
import logging
import secrets
import string
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import get_session
from bot.models.user import User
from bot.models.referral import ReferralEarning, EarningType
from bot.models.subscription import SubscriptionTier, SUBSCRIPTION_FEATURES

logger = logging.getLogger(__name__)

# Referral commission rates
LEVEL_1_RATE = 0.30  # 30% from direct referrals
LEVEL_2_RATE = 0.10  # 10% from second level referrals
FIRST_SUBSCRIPTION_BONUS = 100.0  # Bonus for first paid subscription

# Milestone bonuses
MILESTONE_BONUSES = {
    5: (200.0, EarningType.MILESTONE_5),
    10: (500.0, EarningType.MILESTONE_10),
    25: (1500.0, EarningType.MILESTONE_25),
    50: (5000.0, EarningType.MILESTONE_50),
}


def generate_referral_code(length: int = 8) -> str:
    """Generate unique referral code."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


async def get_or_create_referral_code(user_id: int) -> str:
    """Get existing referral code or create new one."""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User {user_id} not found")
            return None

        if user.referral_code:
            return user.referral_code

        # Generate unique code
        while True:
            code = generate_referral_code()
            existing = await session.execute(
                select(User).where(User.referral_code == code)
            )
            if not existing.scalar_one_or_none():
                break

        user.referral_code = code
        await session.commit()

        logger.info(f"Generated referral code {code} for user {user_id}")
        return code


async def register_referral(user_id: int, referral_code: str) -> bool:
    """
    Register user as referral using referral code.

    Returns:
        True if successfully registered, False otherwise
    """
    async with get_session() as session:
        # Find referrer by code
        result = await session.execute(
            select(User).where(User.referral_code == referral_code)
        )
        referrer = result.scalar_one_or_none()

        if not referrer:
            logger.warning(f"Referral code {referral_code} not found")
            return False

        # Find new user
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User {user_id} not found")
            return False

        # Check if user already has referrer
        if user.referrer_id:
            logger.warning(f"User {user_id} already has referrer")
            return False

        # Check self-referral
        if referrer.telegram_id == user_id:
            logger.warning(f"User {user_id} tried to use own referral code")
            return False

        # Register referral
        user.referrer_id = referrer.id
        await session.commit()

        # Check and award milestone bonuses
        await check_milestone_bonuses(session, referrer)
        await session.commit()

        logger.info(f"User {user_id} registered as referral of {referrer.telegram_id}")
        return True


async def process_subscription_payment(
    user_id: int,
    tier: SubscriptionTier,
    amount: float
) -> None:
    """
    Process referral earnings when user purchases subscription.

    Args:
        user_id: User who purchased subscription
        tier: Subscription tier
        amount: Payment amount in rubles
    """
    async with get_session() as session:
        # Find user
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.referrer_id:
            return

        # Find referrer (level 1)
        result = await session.execute(
            select(User).where(User.id == user.referrer_id)
        )
        referrer_l1 = result.scalar_one_or_none()

        if not referrer_l1:
            return

        # Level 1 commission (30%)
        level_1_amount = amount * LEVEL_1_RATE
        referrer_l1.referral_balance += level_1_amount

        earning_l1 = ReferralEarning(
            user_id=referrer_l1.id,
            amount=level_1_amount,
            earning_type=EarningType.LEVEL_1,
            from_user_id=user.id,
            subscription_tier=tier.value
        )
        session.add(earning_l1)

        logger.info(f"Level 1: User {referrer_l1.telegram_id} earned {level_1_amount}₽ from {user_id}")

        # Check if this is first paid subscription for referrer
        result = await session.execute(
            select(func.count(ReferralEarning.id))
            .where(
                ReferralEarning.user_id == referrer_l1.id,
                ReferralEarning.earning_type.in_([EarningType.LEVEL_1, EarningType.LEVEL_2])
            )
        )
        earnings_count = result.scalar()

        if earnings_count == 0:  # First earning
            referrer_l1.referral_balance += FIRST_SUBSCRIPTION_BONUS
            bonus_earning = ReferralEarning(
                user_id=referrer_l1.id,
                amount=FIRST_SUBSCRIPTION_BONUS,
                earning_type=EarningType.FIRST_SUBSCRIPTION_BONUS,
                from_user_id=user.id
            )
            session.add(bonus_earning)
            logger.info(f"First subscription bonus: {referrer_l1.telegram_id} earned {FIRST_SUBSCRIPTION_BONUS}₽")

        # Check milestone bonuses for level 1
        await check_milestone_bonuses(session, referrer_l1)

        # Level 2 commission (10%) if referrer has referrer
        if referrer_l1.referrer_id:
            result = await session.execute(
                select(User).where(User.id == referrer_l1.referrer_id)
            )
            referrer_l2 = result.scalar_one_or_none()

            if referrer_l2:
                level_2_amount = amount * LEVEL_2_RATE
                referrer_l2.referral_balance += level_2_amount

                earning_l2 = ReferralEarning(
                    user_id=referrer_l2.id,
                    amount=level_2_amount,
                    earning_type=EarningType.LEVEL_2,
                    from_user_id=user.id,
                    subscription_tier=tier.value
                )
                session.add(earning_l2)

                logger.info(f"Level 2: User {referrer_l2.telegram_id} earned {level_2_amount}₽ from {user_id}")

        await session.commit()


async def check_milestone_bonuses(session: AsyncSession, user: User) -> None:
    """Check and award milestone bonuses."""
    # Count total referrals
    result = await session.execute(
        select(func.count(User.id)).where(User.referrer_id == user.id)
    )
    referral_count = result.scalar()

    # Check each milestone
    for milestone, (bonus_amount, earning_type) in MILESTONE_BONUSES.items():
        if referral_count >= milestone:
            # Check if already awarded
            result = await session.execute(
                select(ReferralEarning)
                .where(
                    ReferralEarning.user_id == user.id,
                    ReferralEarning.earning_type == earning_type
                )
            )
            if not result.scalar_one_or_none():
                user.referral_balance += bonus_amount
                bonus_earning = ReferralEarning(
                    user_id=user.id,
                    amount=bonus_amount,
                    earning_type=earning_type
                )
                session.add(bonus_earning)
                logger.info(f"Milestone bonus: User {user.telegram_id} earned {bonus_amount}₽ for {milestone} referrals")


async def withdraw_from_balance(user_id: int, amount: float) -> bool:
    """
    Withdraw amount from referral balance.

    Returns:
        True if successful, False if insufficient balance
    """
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False

        if user.referral_balance < amount:
            return False

        user.referral_balance -= amount

        # Record withdrawal
        withdrawal = ReferralEarning(
            user_id=user.id,
            amount=-amount,
            earning_type=EarningType.WITHDRAWAL
        )
        session.add(withdrawal)

        await session.commit()
        logger.info(f"User {user_id} withdrew {amount}₽ from referral balance")
        return True


async def get_referral_stats(user_id: int) -> dict:
    """Get referral statistics for user."""
    async with get_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Count level 1 referrals
        result = await session.execute(
            select(func.count(User.id)).where(User.referrer_id == user.id)
        )
        level_1_count = result.scalar()

        # Count level 2 referrals (referrals of my referrals)
        # First get IDs of level 1 referrals
        result = await session.execute(
            select(User.id).where(User.referrer_id == user.id)
        )
        level_1_ids = [row[0] for row in result.all()]

        # Then count users who have level 1 referrals as their referrer
        level_2_count = 0
        if level_1_ids:
            result = await session.execute(
                select(func.count(User.id)).where(User.referrer_id.in_(level_1_ids))
            )
            level_2_count = result.scalar() or 0

        # Total earnings
        result = await session.execute(
            select(func.sum(ReferralEarning.amount))
            .where(
                ReferralEarning.user_id == user.id,
                ReferralEarning.earning_type != EarningType.WITHDRAWAL
            )
        )
        total_earned = result.scalar() or 0.0

        # Total withdrawn
        result = await session.execute(
            select(func.sum(ReferralEarning.amount))
            .where(
                ReferralEarning.user_id == user.id,
                ReferralEarning.earning_type == EarningType.WITHDRAWAL
            )
        )
        total_withdrawn = abs(result.scalar() or 0.0)

        return {
            "referral_code": user.referral_code,
            "balance": user.referral_balance,
            "level_1_count": level_1_count,
            "level_2_count": level_2_count,
            "total_referrals": level_1_count + level_2_count,
            "total_earned": total_earned,
            "total_withdrawn": total_withdrawn
        }


async def get_balance(user_id: int) -> float:
    """Get user's referral balance."""
    async with get_session() as session:
        result = await session.execute(
            select(User.referral_balance).where(User.telegram_id == user_id)
        )
        balance = result.scalar_one_or_none()
        return balance or 0.0
