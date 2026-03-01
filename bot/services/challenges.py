"""Challenge service - weekly challenge management."""
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_

from bot.database.db import get_session
from bot.models.challenge import UserChallenge, ChallengeType, CHALLENGE_TEMPLATES
from bot.models.shift import Shift

logger = logging.getLogger(__name__)


def _get_week_bounds() -> tuple[datetime, datetime]:
    """Get current week start (Monday) and end (Sunday)."""
    now = datetime.now()
    # Monday = 0, Sunday = 6
    days_since_monday = now.weekday()
    week_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    return week_start, week_end


async def get_or_create_weekly_challenge(user_id: int) -> UserChallenge:
    """
    Get user's current weekly challenge or create a new one.

    Args:
        user_id: User ID

    Returns:
        UserChallenge object
    """
    week_start, week_end = _get_week_bounds()

    async with get_session() as session:
        # Check if user has active challenge for this week
        result = await session.execute(
            select(UserChallenge).where(
                and_(
                    UserChallenge.user_id == user_id,
                    UserChallenge.week_start == week_start
                )
            )
        )
        challenge = result.scalar_one_or_none()

        if challenge:
            return challenge

        # Create new challenge for this week
        challenge_type = _select_challenge_type(user_id)
        template = CHALLENGE_TEMPLATES[challenge_type]

        # Select difficulty based on user's history (for now, random)
        difficulty_index = random.randint(0, len(template["targets"]) - 1)
        target = template["targets"][difficulty_index]
        reward = template["rewards"][difficulty_index]

        challenge = UserChallenge(
            user_id=user_id,
            challenge_type=challenge_type.value,
            target=float(target),
            progress=0.0,
            reward_description=reward,
            week_start=week_start,
            week_end=week_end,
            is_completed=False
        )

        session.add(challenge)
        await session.commit()
        await session.refresh(challenge)

        logger.info(f"Created new challenge for user {user_id}: {challenge_type.value} (target: {target})")
        return challenge


def _select_challenge_type(user_id: int) -> ChallengeType:
    """Select appropriate challenge type for user."""
    # For now, random selection
    # TODO: Analyze user's history and select appropriate challenge
    return random.choice(list(ChallengeType))


async def update_challenge_progress(user_id: int, shift: Shift) -> Optional[UserChallenge]:
    """
    Update challenge progress after shift completion.

    Args:
        user_id: User ID
        shift: Completed shift

    Returns:
        UserChallenge if completed, None otherwise
    """
    challenge = await get_or_create_weekly_challenge(user_id)

    if challenge.is_completed or not challenge.is_active:
        return None

    async with get_session() as session:
        # Merge challenge into session
        challenge = await session.merge(challenge)

        # Update progress based on challenge type
        challenge_type = ChallengeType(challenge.challenge_type)

        if challenge_type == ChallengeType.EARNINGS:
            challenge.progress += shift.net_earnings
        elif challenge_type == ChallengeType.SHIFTS:
            challenge.progress += 1
        elif challenge_type == ChallengeType.HOURS:
            challenge.progress += shift.duration_hours
        elif challenge_type == ChallengeType.TRIPS:
            challenge.progress += shift.trips_count
        elif challenge_type == ChallengeType.DISTANCE:
            challenge.progress += shift.distance_km
        elif challenge_type == ChallengeType.NIGHT_SHIFTS:
            # Check if shift started at night (22:00-06:00)
            hour = shift.start_time.hour
            if hour >= 22 or hour < 6:
                challenge.progress += 1
        elif challenge_type == ChallengeType.HIGH_RATE:
            # For rate challenges, track the highest rate achieved
            if shift.hourly_rate > challenge.progress:
                challenge.progress = shift.hourly_rate

        # Check if completed
        if challenge.progress >= challenge.target and not challenge.is_completed:
            challenge.is_completed = True
            challenge.completed_at = datetime.now()
            await session.commit()
            await session.refresh(challenge)
            logger.info(f"User {user_id} completed challenge: {challenge_type.value}")
            return challenge

        await session.commit()
        await session.refresh(challenge)
        return None


async def get_challenge_stats(user_id: int) -> dict:
    """
    Get user's challenge statistics.

    Returns:
        Dict with total_completed, current_streak, etc.
    """
    async with get_session() as session:
        # Count completed challenges
        result = await session.execute(
            select(UserChallenge).where(
                and_(
                    UserChallenge.user_id == user_id,
                    UserChallenge.is_completed == True
                )
            )
        )
        completed_challenges = result.scalars().all()

        return {
            "total_completed": len(completed_challenges),
            "has_history": len(completed_challenges) > 0
        }


def format_challenge(challenge: UserChallenge) -> str:
    """Format challenge as text."""
    template = CHALLENGE_TEMPLATES[ChallengeType(challenge.challenge_type)]

    # Format target based on challenge type
    challenge_type = ChallengeType(challenge.challenge_type)
    if challenge_type in [ChallengeType.EARNINGS, ChallengeType.HIGH_RATE]:
        target_str = f"{challenge.target:.0f}₽"
        progress_str = f"{challenge.progress:.0f}₽"
    elif challenge_type in [ChallengeType.HOURS]:
        target_str = f"{challenge.target:.0f} ч"
        progress_str = f"{challenge.progress:.1f} ч"
    elif challenge_type == ChallengeType.DISTANCE:
        target_str = f"{challenge.target:.0f} км"
        progress_str = f"{challenge.progress:.0f} км"
    else:
        target_str = f"{challenge.target:.0f}"
        progress_str = f"{challenge.progress:.0f}"

    # Progress bar
    percentage = challenge.progress_percentage
    filled = int(percentage / 10)
    bar = "█" * filled + "░" * (10 - filled)

    # Status
    if challenge.is_completed:
        status = "✅ Завершено!"
    elif not challenge.is_active:
        status = "⏰ Истекло"
    else:
        days_left = (challenge.week_end - datetime.now()).days
        status = f"⏳ Осталось {days_left} дн."

    description = template["description"].format(target=challenge.target)

    text = (
        f"{template['emoji']} <b>{template['name']}</b>\n"
        f"{description}\n\n"
        f"Прогресс: {progress_str} / {target_str}\n"
        f"{bar} {percentage:.0f}%\n\n"
        f"{status}\n"
        f"🎁 Награда: {challenge.reward_description}"
    )

    return text


def format_challenge_completion(challenge: UserChallenge) -> str:
    """Format challenge completion notification."""
    template = CHALLENGE_TEMPLATES[ChallengeType(challenge.challenge_type)]

    return (
        f"🎉 <b>ЧЕЛЛЕНДЖ ЗАВЕРШЁН!</b>\n\n"
        f"{template['emoji']} <b>{template['name']}</b>\n\n"
        f"Вы выполнили недельный челлендж и получили награду:\n"
        f"🎁 <b>{challenge.reward_description}</b>\n\n"
        f"Продолжайте в том же духе! 💪"
    )
