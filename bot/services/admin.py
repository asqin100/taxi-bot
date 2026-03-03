"""Admin panel service - statistics and management."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import select, func, and_

from bot.database.db import get_session
from bot.models.user import User
from bot.models.shift import Shift
from bot.models.subscription import Subscription, SubscriptionTier
from bot.models.achievement import UserAchievement
from bot.models.challenge import UserChallenge

logger = logging.getLogger(__name__)


async def get_dashboard_stats() -> Dict:
    """Get statistics for admin dashboard."""
    async with get_session() as session:
        # Total users
        total_users = await session.scalar(select(func.count(User.id)))

        # Active users (users with shifts in last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        active_users_result = await session.execute(
            select(func.count(func.distinct(Shift.user_id)))
            .where(Shift.start_time >= week_ago)
        )
        active_users = active_users_result.scalar() or 0

        # New users today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        new_users_today = await session.scalar(
            select(func.count(User.id)).where(User.created_at >= today)
        )

        # Subscriptions by tier
        free_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                Subscription.tier == SubscriptionTier.FREE.value
            )
        )
        pro_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.tier == SubscriptionTier.PRO.value,
                    Subscription.is_active == True
                )
            )
        )
        premium_subs = await session.scalar(
            select(func.count(Subscription.id)).where(
                and_(
                    Subscription.tier == SubscriptionTier.PREMIUM.value,
                    Subscription.is_active == True
                )
            )
        )

        # Total shifts
        total_shifts = await session.scalar(select(func.count(Shift.id)))

        # Shifts today
        shifts_today = await session.scalar(
            select(func.count(Shift.id)).where(Shift.start_time >= today)
        )

        # Total earnings (all time)
        total_earnings = await session.scalar(
            select(func.sum(Shift.gross_earnings)).where(Shift.gross_earnings.isnot(None))
        ) or 0

        # Achievements unlocked
        total_achievements = await session.scalar(
            select(func.count(UserAchievement.id)).where(
                UserAchievement.unlocked_at.isnot(None)
            )
        )

        # Active challenges
        active_challenges = await session.scalar(
            select(func.count(UserChallenge.id)).where(
                and_(
                    UserChallenge.is_completed == False,
                    UserChallenge.week_end >= datetime.now()
                )
            )
        )

        return {
            "users": {
                "total": total_users or 0,
                "active": active_users or 0,
                "new_today": new_users_today or 0
            },
            "subscriptions": {
                "free": free_subs or 0,
                "pro": pro_subs or 0,
                "premium": premium_subs or 0
            },
            "shifts": {
                "total": total_shifts or 0,
                "today": shifts_today or 0,
                "total_earnings": float(total_earnings)
            },
            "gamification": {
                "achievements": total_achievements or 0,
                "active_challenges": active_challenges or 0
            }
        }


async def get_recent_users(limit: int = 10) -> List[Dict]:
    """Get recently registered users."""
    async with get_session() as session:
        result = await session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        users = result.scalars().all()

        return [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]


async def get_top_earners(limit: int = 10) -> List[Dict]:
    """Get top earning users."""
    async with get_session() as session:
        result = await session.execute(
            select(
                User.telegram_id,
                User.username,
                func.sum(Shift.gross_earnings).label("total_earnings"),
                func.count(Shift.id).label("shift_count")
            )
            .join(Shift, User.telegram_id == Shift.user_id)
            .group_by(User.telegram_id, User.username)
            .order_by(func.sum(Shift.gross_earnings).desc())
            .limit(limit)
        )

        return [
            {
                "telegram_id": row.telegram_id,
                "username": row.username or "Unknown",
                "total_earnings": float(row.total_earnings or 0),
                "shift_count": row.shift_count
            }
            for row in result
        ]


async def search_users(query: str, limit: int = 20) -> List[Dict]:
    """Search users by username or telegram_id."""
    async with get_session() as session:
        # Try to parse as telegram_id
        try:
            telegram_id = int(query)
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
        except ValueError:
            # Search by username
            result = await session.execute(
                select(User)
                .where(User.username.ilike(f"%{query}%"))
                .limit(limit)
            )

        users = result.scalars().all()

        return [
            {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username or "Unknown",
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]


async def get_user_details(telegram_id: int) -> Dict:
    """Get detailed user information."""
    async with get_session() as session:
        # Get user
        user_result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        # Get subscription
        sub_result = await session.execute(
            select(Subscription).where(Subscription.user_id == telegram_id)
        )
        subscription = sub_result.scalar_one_or_none()

        # Get shifts count and total earnings
        shifts_result = await session.execute(
            select(
                func.count(Shift.id).label("shift_count"),
                func.sum(Shift.gross_earnings).label("total_earnings")
            )
            .where(Shift.user_id == telegram_id)
        )
        shifts_data = shifts_result.one()

        # Get achievements count
        achievements_count = await session.scalar(
            select(func.count(UserAchievement.id))
            .where(
                and_(
                    UserAchievement.user_id == telegram_id,
                    UserAchievement.unlocked_at.isnot(None)
                )
            )
        ) or 0

        return {
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username or "Unknown",
                "created_at": user.created_at.isoformat()
            },
            "subscription": {
                "tier": subscription.tier if subscription else "free",
                "is_active": subscription.is_active if subscription else True,
                "expires_at": subscription.expires_at.isoformat() if subscription and subscription.expires_at else None
            } if subscription else None,
            "stats": {
                "shift_count": shifts_data.shift_count or 0,
                "total_earnings": float(shifts_data.total_earnings or 0),
                "achievements": achievements_count
            }
        }


async def grant_subscription(telegram_id: int, tier: str, duration_days: int = 30) -> bool:
    """Grant or upgrade user subscription."""
    from bot.services.subscription import upgrade_subscription
    from bot.models.subscription import SubscriptionTier

    try:
        tier_enum = SubscriptionTier(tier)
        await upgrade_subscription(
            user_id=telegram_id,
            tier=tier_enum,
            duration_days=duration_days,
            payment_method="admin_grant"
        )
        logger.info(f"Admin granted {tier} subscription to user {telegram_id}")
        return True
    except Exception as e:
        logger.error(f"Error granting subscription: {e}")
        return False


async def reset_user_data(telegram_id: int) -> bool:
    """Reset user data to initial state (as if first time entering bot)."""
    from bot.models.financial_settings import UserFinancialSettings
    from bot.models.ai_usage import AIUsage
    from bot.models.referral import ReferralEarning

    try:
        async with get_session() as session:
            # Get user
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {telegram_id} not found for reset")
                return False

            # Delete related records
            # Delete shifts
            await session.execute(
                Shift.__table__.delete().where(Shift.user_id == telegram_id)
            )

            # Delete subscriptions
            await session.execute(
                Subscription.__table__.delete().where(Subscription.user_id == telegram_id)
            )

            # Delete achievements
            await session.execute(
                UserAchievement.__table__.delete().where(UserAchievement.user_id == telegram_id)
            )

            # Delete challenges
            await session.execute(
                UserChallenge.__table__.delete().where(UserChallenge.user_id == telegram_id)
            )

            # Delete financial settings
            await session.execute(
                UserFinancialSettings.__table__.delete().where(UserFinancialSettings.user_id == telegram_id)
            )

            # Delete AI usage records
            await session.execute(
                AIUsage.__table__.delete().where(AIUsage.user_id == telegram_id)
            )

            # Delete referral earnings (where user earned)
            await session.execute(
                ReferralEarning.__table__.delete().where(ReferralEarning.user_id == telegram_id)
            )

            # Delete referral earnings (where others earned from this user)
            await session.execute(
                ReferralEarning.__table__.delete().where(ReferralEarning.from_user_id == user.id)
            )

            # Clear referrer_id for users who have this user as referrer
            await session.execute(
                User.__table__.update()
                .where(User.referrer_id == user.id)
                .values(referrer_id=None)
            )

            # Generate new referral code
            from bot.services.referral import generate_referral_code
            while True:
                new_code = generate_referral_code()
                existing = await session.execute(
                    select(User).where(User.referral_code == new_code)
                )
                if not existing.scalar_one_or_none():
                    break

            # Reset user settings to defaults
            user.tariffs = "econom"
            user.zones = ""
            user.notify_enabled = False
            user.surge_threshold = 1.5
            user.event_notify_enabled = True
            user.event_types = "concert,sport"
            user.quiet_hours_enabled = False
            user.quiet_hours_start = 22
            user.quiet_hours_end = 7
            user.geo_alerts_enabled = False
            user.last_latitude = None
            user.last_longitude = None
            user.last_location_update = None
            user.live_location_expires_at = None
            user.onboarding_completed = False
            user.referral_balance = 0.0
            user.referrer_id = None
            user.referral_code = new_code

            await session.commit()

            logger.info(f"Admin reset user data for {telegram_id}")
            return True

    except Exception as e:
        logger.error(f"Error resetting user data: {e}")
        return False


async def delete_user_permanently(telegram_id: int) -> bool:
    """Permanently delete user and all related data from database."""
    from bot.models.financial_settings import UserFinancialSettings
    from bot.models.ai_usage import AIUsage
    from bot.models.referral import ReferralEarning

    try:
        async with get_session() as session:
            # Get user
            user_result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                logger.warning(f"User {telegram_id} not found for deletion")
                return False

            # Clear referrer_id for users who have this user as referrer
            await session.execute(
                User.__table__.update()
                .where(User.referrer_id == user.id)
                .values(referrer_id=None)
            )

            # Delete all related records
            # Delete shifts
            await session.execute(
                Shift.__table__.delete().where(Shift.user_id == telegram_id)
            )

            # Delete subscriptions
            await session.execute(
                Subscription.__table__.delete().where(Subscription.user_id == telegram_id)
            )

            # Delete achievements
            await session.execute(
                UserAchievement.__table__.delete().where(UserAchievement.user_id == telegram_id)
            )

            # Delete challenges
            await session.execute(
                UserChallenge.__table__.delete().where(UserChallenge.user_id == telegram_id)
            )

            # Delete financial settings
            await session.execute(
                UserFinancialSettings.__table__.delete().where(UserFinancialSettings.user_id == telegram_id)
            )

            # Delete AI usage records
            await session.execute(
                AIUsage.__table__.delete().where(AIUsage.user_id == telegram_id)
            )

            # Delete referral earnings (where user earned)
            await session.execute(
                ReferralEarning.__table__.delete().where(ReferralEarning.user_id == user.id)
            )

            # Delete referral earnings (where others earned from this user)
            await session.execute(
                ReferralEarning.__table__.delete().where(ReferralEarning.from_user_id == user.id)
            )

            # Finally, delete the user
            await session.execute(
                User.__table__.delete().where(User.telegram_id == telegram_id)
            )

            await session.commit()

            logger.info(f"Admin permanently deleted user {telegram_id}")
            return True

    except Exception as e:
        logger.error(f"Error deleting user permanently: {e}")
        return False


async def get_all_user_ids() -> List[int]:
    """Get all user telegram IDs for broadcast."""
    async with get_session() as session:
        result = await session.execute(
            select(User.telegram_id)
        )
        return [row[0] for row in result.all()]
