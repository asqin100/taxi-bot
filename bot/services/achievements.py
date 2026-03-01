"""Achievement service - manage user achievements and progress."""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import get_session
from bot.models.achievement import UserAchievement, AchievementType, ACHIEVEMENTS
from bot.models.shift import Shift

logger = logging.getLogger(__name__)


async def initialize_achievements(user_id: int):
    """Initialize all achievements for a new user."""
    async with get_session() as session:
        for achievement_type, config in ACHIEVEMENTS.items():
            # Check if already exists
            result = await session.execute(
                select(UserAchievement).where(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_type == achievement_type.value
                )
            )
            existing = result.scalar_one_or_none()

            if not existing:
                achievement = UserAchievement(
                    user_id=user_id,
                    achievement_type=achievement_type.value,
                    progress=0,
                    target=config["target"],
                    is_unlocked=False
                )
                session.add(achievement)

        await session.commit()
        logger.info("Initialized achievements for user %d", user_id)


async def get_user_achievements(user_id: int) -> list[UserAchievement]:
    """Get all achievements for a user."""
    async with get_session() as session:
        result = await session.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        achievements = result.scalars().all()

        # Initialize if empty
        if not achievements:
            await initialize_achievements(user_id)
            result = await session.execute(
                select(UserAchievement).where(UserAchievement.user_id == user_id)
            )
            achievements = result.scalars().all()

        return list(achievements)


async def update_achievement_progress(
    user_id: int,
    achievement_type: AchievementType,
    increment: int = 1
) -> Optional[UserAchievement]:
    """Update achievement progress and check if unlocked."""
    async with get_session() as session:
        result = await session.execute(
            select(UserAchievement).where(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_type == achievement_type.value
            )
        )
        achievement = result.scalar_one_or_none()

        if not achievement:
            # Create if doesn't exist
            config = ACHIEVEMENTS[achievement_type]
            achievement = UserAchievement(
                user_id=user_id,
                achievement_type=achievement_type.value,
                progress=0,
                target=config["target"],
                is_unlocked=False
            )
            session.add(achievement)

        if not achievement.is_unlocked:
            achievement.progress += increment

            # Check if unlocked
            if achievement.progress >= achievement.target:
                achievement.is_unlocked = True
                achievement.unlocked_at = datetime.now()
                await session.commit()
                await session.refresh(achievement)
                logger.info("User %d unlocked achievement: %s", user_id, achievement_type.value)
                return achievement

        await session.commit()
        await session.refresh(achievement)
        return None


async def check_shift_achievements(user_id: int, shift: Shift):
    """Check and update achievements based on completed shift."""
    unlocked = []

    # First shift
    if shift.id == 1:
        achievement = await update_achievement_progress(user_id, AchievementType.FIRST_SHIFT)
        if achievement:
            unlocked.append(achievement)

    # Night owl (22:00-06:00)
    start_hour = shift.start_time.hour
    if 22 <= start_hour or start_hour < 6:
        achievement = await update_achievement_progress(user_id, AchievementType.NIGHT_OWL)
        if achievement:
            unlocked.append(achievement)

    # Early bird (06:00-10:00)
    if 6 <= start_hour < 10:
        achievement = await update_achievement_progress(user_id, AchievementType.EARLY_BIRD)
        if achievement:
            unlocked.append(achievement)

    # Marathon (12+ hours)
    if shift.duration_hours >= 12:
        achievement = await update_achievement_progress(user_id, AchievementType.MARATHON)
        if achievement:
            unlocked.append(achievement)

    # Efficient (1500₽/hour)
    if shift.hourly_rate >= 1500:
        achievement = await update_achievement_progress(user_id, AchievementType.EFFICIENT)
        if achievement:
            unlocked.append(achievement)

    # Millionaire (total earnings)
    achievement = await update_achievement_progress(
        user_id,
        AchievementType.MILLIONAIRE,
        increment=int(shift.net_earnings)
    )
    if achievement:
        unlocked.append(achievement)

    # Consistent (30 shifts)
    achievement = await update_achievement_progress(user_id, AchievementType.CONSISTENT)
    if achievement:
        unlocked.append(achievement)

    return unlocked


def format_achievement(achievement: UserAchievement) -> str:
    """Format single achievement as text."""
    config = ACHIEVEMENTS.get(AchievementType(achievement.achievement_type), {})
    emoji = config.get("emoji", "🏆")
    name = config.get("name", "Unknown")
    description = config.get("description", "")

    if achievement.is_unlocked:
        return f"{emoji} <b>{name}</b> ✅\n   <i>{description}</i>"
    else:
        progress_bar = _create_progress_bar(achievement.progress, achievement.target)
        return (
            f"{emoji} <b>{name}</b>\n"
            f"   <i>{description}</i>\n"
            f"   {progress_bar} {achievement.progress}/{achievement.target}"
        )


def _create_progress_bar(current: int, target: int, length: int = 10) -> str:
    """Create a visual progress bar."""
    if target == 0:
        filled = length
    else:
        filled = int((current / target) * length)
    filled = min(filled, length)
    empty = length - filled
    return "█" * filled + "░" * empty


def format_achievements_list(achievements: list[UserAchievement]) -> str:
    """Format all achievements as text."""
    unlocked = [a for a in achievements if a.is_unlocked]
    locked = [a for a in achievements if not a.is_unlocked]

    lines = ["🏆 <b>ДОСТИЖЕНИЯ</b>\n"]

    if unlocked:
        lines.append(f"<b>Разблокировано ({len(unlocked)}/{len(achievements)}):</b>\n")
        for achievement in unlocked:
            lines.append(format_achievement(achievement))
            lines.append("")

    if locked:
        lines.append("<b>В процессе:</b>\n")
        for achievement in locked[:5]:  # Show top 5 in progress
            lines.append(format_achievement(achievement))
            lines.append("")

    return "\n".join(lines)


def format_achievement_unlock(achievement: UserAchievement) -> str:
    """Format achievement unlock notification."""
    config = ACHIEVEMENTS.get(AchievementType(achievement.achievement_type), {})
    emoji = config.get("emoji", "🏆")
    name = config.get("name", "Unknown")
    reward = config.get("reward", "")

    return (
        f"🎉 <b>ДОСТИЖЕНИЕ РАЗБЛОКИРОВАНО!</b>\n\n"
        f"{emoji} <b>{name}</b>\n\n"
        f"<i>{reward}</i>"
    )
