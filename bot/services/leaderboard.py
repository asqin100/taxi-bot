"""Leaderboard service - anonymous driver rankings and game leaderboard."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, func, and_

from bot.database.db import get_session
from bot.models.shift import Shift
from bot.models.user import User
from bot.models.referral import ReferralEarning, EarningType

logger = logging.getLogger(__name__)


class LeaderboardEntry:
    """Leaderboard entry with anonymous driver info."""
    def __init__(self, rank: int, anonymous_name: str, value: float, is_current_user: bool = False):
        self.rank = rank
        self.anonymous_name = anonymous_name
        self.value = value
        self.is_current_user = is_current_user


def _generate_anonymous_name(user_id: int) -> str:
    """Generate consistent anonymous name for user."""
    # Use user_id to generate consistent but anonymous name
    animals = ["Лев", "Тигр", "Орел", "Волк", "Медведь", "Сокол", "Пантера", "Ягуар", "Барс", "Рысь"]
    colors = ["Красный", "Синий", "Зеленый", "Золотой", "Серебряный", "Черный", "Белый", "Фиолетовый"]

    animal_idx = user_id % len(animals)
    color_idx = (user_id // len(animals)) % len(colors)
    number = (user_id % 999) + 1

    return f"{colors[color_idx]} {animals[animal_idx]} #{number}"


async def get_earnings_leaderboard(period: str = "week", limit: int = 10, user_id: Optional[int] = None) -> list[LeaderboardEntry]:
    """
    Get leaderboard by earnings.

    Args:
        period: "week", "month", or "all"
        limit: Number of top entries to return
        user_id: Current user ID to highlight their position

    Returns:
        List of LeaderboardEntry objects
    """
    async with get_session() as session:
        # Calculate date cutoff
        if period == "week":
            cutoff = datetime.now() - timedelta(days=7)
        elif period == "month":
            cutoff = datetime.now() - timedelta(days=30)
        else:
            cutoff = datetime.min

        # Query top earners
        query = (
            select(
                Shift.user_id,
                func.sum(Shift.net_earnings).label("total_earnings")
            )
            .where(
                and_(
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
            .group_by(Shift.user_id)
            .order_by(func.sum(Shift.net_earnings).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        top_users = result.all()

        # Build leaderboard
        leaderboard = []
        for rank, (uid, earnings) in enumerate(top_users, start=1):
            is_current = uid == user_id
            anonymous_name = _generate_anonymous_name(uid)
            leaderboard.append(LeaderboardEntry(rank, anonymous_name, earnings, is_current))

        # If current user not in top, add their position
        if user_id and not any(e.is_current_user for e in leaderboard):
            user_entry = await _get_user_position(session, user_id, cutoff, "earnings")
            if user_entry:
                leaderboard.append(user_entry)

        return leaderboard


async def get_hours_leaderboard(period: str = "week", limit: int = 10, user_id: Optional[int] = None) -> list[LeaderboardEntry]:
    """Get leaderboard by hours worked."""
    async with get_session() as session:
        if period == "week":
            cutoff = datetime.now() - timedelta(days=7)
        elif period == "month":
            cutoff = datetime.now() - timedelta(days=30)
        else:
            cutoff = datetime.min

        query = (
            select(
                Shift.user_id,
                func.sum(Shift.duration_hours).label("total_hours")
            )
            .where(
                and_(
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
            .group_by(Shift.user_id)
            .order_by(func.sum(Shift.duration_hours).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        top_users = result.all()

        leaderboard = []
        for rank, (uid, hours) in enumerate(top_users, start=1):
            is_current = uid == user_id
            anonymous_name = _generate_anonymous_name(uid)
            leaderboard.append(LeaderboardEntry(rank, anonymous_name, hours, is_current))

        if user_id and not any(e.is_current_user for e in leaderboard):
            user_entry = await _get_user_position(session, user_id, cutoff, "hours")
            if user_entry:
                leaderboard.append(user_entry)

        return leaderboard


async def get_efficiency_leaderboard(period: str = "week", limit: int = 10, user_id: Optional[int] = None) -> list[LeaderboardEntry]:
    """Get leaderboard by average hourly rate."""
    async with get_session() as session:
        if period == "week":
            cutoff = datetime.now() - timedelta(days=7)
        elif period == "month":
            cutoff = datetime.now() - timedelta(days=30)
        else:
            cutoff = datetime.min

        # Only include users with at least 3 shifts for fair comparison
        query = (
            select(
                Shift.user_id,
                func.avg(Shift.hourly_rate).label("avg_rate"),
                func.count(Shift.id).label("shift_count")
            )
            .where(
                and_(
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
            .group_by(Shift.user_id)
            .having(func.count(Shift.id) >= 3)
            .order_by(func.avg(Shift.hourly_rate).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        top_users = result.all()

        leaderboard = []
        for rank, (uid, avg_rate, shift_count) in enumerate(top_users, start=1):
            is_current = uid == user_id
            anonymous_name = _generate_anonymous_name(uid)
            leaderboard.append(LeaderboardEntry(rank, anonymous_name, avg_rate, is_current))

        if user_id and not any(e.is_current_user for e in leaderboard):
            user_entry = await _get_user_position(session, user_id, cutoff, "efficiency")
            if user_entry:
                leaderboard.append(user_entry)

        return leaderboard


async def _get_user_position(session, user_id: int, cutoff: datetime, metric: str) -> Optional[LeaderboardEntry]:
    """Get user's position in leaderboard if not in top."""
    if metric == "earnings":
        # Get user's total earnings
        result = await session.execute(
            select(func.sum(Shift.net_earnings))
            .where(
                and_(
                    Shift.user_id == user_id,
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
        )
        user_value = result.scalar() or 0

        # Count how many users have more
        result = await session.execute(
            select(func.count(func.distinct(Shift.user_id)))
            .where(
                and_(
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
            .group_by(Shift.user_id)
            .having(func.sum(Shift.net_earnings) > user_value)
        )
        rank = len(result.all()) + 1

    elif metric == "hours":
        result = await session.execute(
            select(func.sum(Shift.duration_hours))
            .where(
                and_(
                    Shift.user_id == user_id,
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
        )
        user_value = result.scalar() or 0
        rank = 0  # Simplified for now

    else:  # efficiency
        result = await session.execute(
            select(func.avg(Shift.hourly_rate), func.count(Shift.id))
            .where(
                and_(
                    Shift.user_id == user_id,
                    Shift.end_time.isnot(None),
                    Shift.start_time >= cutoff
                )
            )
        )
        row = result.one_or_none()
        if not row or row[1] < 3:  # Less than 3 shifts
            return None
        user_value = row[0] or 0
        rank = 0  # Simplified

    if user_value == 0:
        return None

    anonymous_name = _generate_anonymous_name(user_id)
    return LeaderboardEntry(rank, anonymous_name, user_value, is_current_user=True)


def format_leaderboard(entries: list[LeaderboardEntry], metric: str, period: str) -> str:
    """Format leaderboard as text."""
    # Title
    if metric == "earnings":
        title = "💰 Рейтинг по заработку"
        unit = "₽"
    elif metric == "hours":
        title = "⏱ Рейтинг по часам"
        unit = " ч"
    else:
        title = "⚡ Рейтинг по эффективности"
        unit = " ₽/ч"

    period_text = {
        "week": "за неделю",
        "month": "за месяц",
        "all": "за всё время"
    }.get(period, "")

    lines = [f"{title} {period_text}\n"]

    # Entries
    for entry in entries[:10]:  # Top 10 only
        medal = ""
        if entry.rank == 1:
            medal = "🥇 "
        elif entry.rank == 2:
            medal = "🥈 "
        elif entry.rank == 3:
            medal = "🥉 "

        highlight = "👉 " if entry.is_current_user else ""
        name_style = f"<b>{entry.anonymous_name}</b>" if entry.is_current_user else entry.anonymous_name

        lines.append(
            f"{highlight}{medal}{entry.rank}. {name_style}: {entry.value:.0f}{unit}"
        )

    # User's position if not in top
    user_entry = next((e for e in entries if e.is_current_user and e.rank > 10), None)
    if user_entry:
        lines.append(f"\n...\n👉 {user_entry.rank}. <b>{user_entry.anonymous_name}</b>: {user_entry.value:.0f}{unit}")

    lines.append("\n🔒 Все имена анонимны")

    return "\n".join(lines)


# Game leaderboard functions

async def get_game_leaderboard(period: str = "all", limit: int = 10) -> list[dict]:
    """
    Get game leaderboard.

    Args:
        period: "day", "week", "month", or "all"
        limit: number of top players to return

    Returns:
        List of dicts with user info and total earnings
    """
    async with get_session() as session:
        # Build time filter
        time_filter = None
        if period == "day":
            time_filter = ReferralEarning.created_at >= datetime.now() - timedelta(days=1)
        elif period == "week":
            time_filter = ReferralEarning.created_at >= datetime.now() - timedelta(weeks=1)
        elif period == "month":
            time_filter = ReferralEarning.created_at >= datetime.now() - timedelta(days=30)

        # Query for top earners from game
        query = (
            select(
                User.telegram_id,
                User.username,
                func.sum(ReferralEarning.amount).label("total_earned"),
                func.count(ReferralEarning.id).label("games_played")
            )
            .join(ReferralEarning, User.id == ReferralEarning.user_id)
            .where(ReferralEarning.earning_type == EarningType.GAME_EARNING)
        )

        if time_filter is not None:
            query = query.where(time_filter)

        query = (
            query
            .group_by(User.telegram_id, User.username)
            .order_by(func.sum(ReferralEarning.amount).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        rows = result.all()

        leaderboard = []
        for idx, row in enumerate(rows, 1):
            leaderboard.append({
                "rank": idx,
                "telegram_id": row.telegram_id,
                "username": row.username or "Аноним",
                "total_earned": round(row.total_earned, 2),
                "games_played": row.games_played
            })

        return leaderboard


async def get_user_game_stats(telegram_id: int) -> dict:
    """Get user's game statistics."""
    async with get_session() as session:
        # Get user
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return {
                "total_earned": 0,
                "games_played": 0,
                "best_earning": 0,
                "rank": None
            }

        # Get total earnings and games played
        result = await session.execute(
            select(
                func.sum(ReferralEarning.amount).label("total_earned"),
                func.count(ReferralEarning.id).label("games_played"),
                func.max(ReferralEarning.amount).label("best_earning")
            )
            .where(
                and_(
                    ReferralEarning.user_id == user.id,
                    ReferralEarning.earning_type == EarningType.GAME_EARNING
                )
            )
        )
        row = result.one()

        total_earned = row.total_earned or 0
        games_played = row.games_played or 0
        best_earning = row.best_earning or 0

        # Get user's rank (count users with more earnings)
        if total_earned > 0:
            rank_query = (
                select(func.count(func.distinct(ReferralEarning.user_id)))
                .where(ReferralEarning.earning_type == EarningType.GAME_EARNING)
                .group_by(ReferralEarning.user_id)
                .having(func.sum(ReferralEarning.amount) > total_earned)
            )
            result = await session.execute(rank_query)
            rank = len(result.all()) + 1
        else:
            rank = None

        return {
            "total_earned": round(total_earned, 2),
            "games_played": games_played,
            "best_earning": round(best_earning, 2),
            "rank": rank
        }


def format_game_leaderboard(leaderboard: list[dict], period: str = "all", current_user_id: int = None) -> str:
    """Format game leaderboard as text."""
    period_names = {
        "day": "за сегодня",
        "week": "за неделю",
        "month": "за месяц",
        "all": "за всё время"
    }

    lines = [f"🏆 <b>ТАБЛИЦА ЛИДЕРОВ ИГРЫ</b> {period_names.get(period, '')}\n"]

    if not leaderboard:
        lines.append("Пока никто не играл 😢\n\nБудь первым! 🎮")
        return "\n".join(lines)

    medals = ["🥇", "🥈", "🥉"]

    for player in leaderboard:
        rank = player["rank"]
        medal = medals[rank - 1] if rank <= 3 else f"{rank}."
        username = player["username"]
        earned = player["total_earned"]
        games = player["games_played"]

        is_current = player["telegram_id"] == current_user_id
        highlight = "👉 " if is_current else ""
        name_style = f"<b>{username}</b>" if is_current else username

        lines.append(
            f"{highlight}{medal} {name_style}\n"
            f"    💰 {earned}₽ • 🎮 {games} игр"
        )

    return "\n".join(lines)
