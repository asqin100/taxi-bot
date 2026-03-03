"""CSV export service for driver shifts."""
import csv
import io
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.shift import Shift
from bot.models.user import User


async def export_shifts_csv(user_id: int, days: int = 30) -> io.StringIO:
    """
    Export user's shifts to CSV format.

    Args:
        user_id: Telegram user ID
        days: Number of days to export (default: 30)

    Returns:
        StringIO object containing CSV data
    """
    from bot.database.db import session_factory

    async with session_factory() as session:
        # Get shifts from last N days
        since = datetime.now() - timedelta(days=days)

        result = await session.execute(
            select(Shift)
            .where(
                Shift.user_id == user_id,
                Shift.start_time >= since,
                Shift.end_time.isnot(None)
            )
            .order_by(Shift.start_time.desc())
        )
        shifts = result.scalars().all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'ID',
            'Дата начала',
            'Дата окончания',
            'Длительность (ч)',
            'Валовый доход (₽)',
            'Чистый доход (₽)',
            'Поездок',
            'Километров',
            'Топливо (₽)',
            'Комиссия (₽)',
            'Аренда (₽)',
            'Прочие расходы (₽)',
            'Заметки'
        ])

        # Write data
        for shift in shifts:
            writer.writerow([
                shift.id,
                shift.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                shift.end_time.strftime("%Y-%m-%d %H:%M:%S") if shift.end_time else "",
                f"{shift.duration_hours:.2f}",
                f"{shift.gross_earnings:.2f}",
                f"{shift.net_earnings:.2f}",
                shift.trips_count,
                f"{shift.distance_km:.2f}",
                f"{shift.fuel_cost:.2f}",
                f"{shift.commission:.2f}",
                f"{shift.rent_cost:.2f}",
                f"{shift.other_expenses:.2f}",
                shift.notes or ""
            ])

        output.seek(0)
        return output


async def check_export_limit(user_id: int) -> tuple[bool, str]:
    """
    Check if user can export based on rate limits.

    Args:
        user_id: Telegram user ID

    Returns:
        Tuple of (can_export: bool, message: str)
    """
    from bot.database.db import session_factory
    from bot.models.user import User

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            return False, "Пользователь не найден"

        # Elite users have unlimited exports
        # Check if user has active subscription with csv_export feature
        if hasattr(user, 'subscription') and user.subscription:
            if user.subscription.is_active and 'csv_export' in user.subscription.features:
                return True, ""

        # For free users: 1 export per day
        if hasattr(user, 'last_export_at') and user.last_export_at:
            time_since_export = datetime.now() - user.last_export_at
            if time_since_export < timedelta(days=1):
                next_available = user.last_export_at + timedelta(days=1)
                return False, f"Следующий экспорт доступен: {next_available.strftime('%Y-%m-%d %H:%M')}"

        return True, ""


async def log_export(user_id: int, shifts_count: int) -> None:
    """
    Log export operation.

    Args:
        user_id: Telegram user ID
        shifts_count: Number of shifts exported
    """
    from bot.database.db import session_factory
    from bot.models.user import User

    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.last_export_at = datetime.now()
            await session.commit()
