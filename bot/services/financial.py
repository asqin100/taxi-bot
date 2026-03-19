"""Financial tracker service - manage shifts and statistics."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import session_factory
from bot.models.shift import Shift
from bot.models.financial_settings import UserFinancialSettings

logger = logging.getLogger(__name__)


async def get_or_create_settings(user_id: int) -> UserFinancialSettings:
    """Get user's financial settings or create default ones."""
    async with session_factory() as session:
        result = await session.execute(
            select(UserFinancialSettings).where(UserFinancialSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = UserFinancialSettings(user_id=user_id)
            session.add(settings)
            await session.commit()
            await session.refresh(settings)

        return settings


async def get_active_shift(user_id: int) -> Optional[Shift]:
    """Get user's currently active shift (not ended)."""
    async with session_factory() as session:
        result = await session.execute(
            select(Shift).where(
                and_(
                    Shift.user_id == user_id,
                    Shift.end_time.is_(None)
                )
            ).order_by(Shift.start_time.desc())
        )
        return result.scalar_one_or_none()


async def start_shift(user_id: int) -> Shift:
    """Start a new shift."""
    async with session_factory() as session:
        shift = Shift(
            user_id=user_id,
            start_time=datetime.now()
        )
        session.add(shift)
        await session.commit()
        await session.refresh(shift)
        logger.info("Started shift for user %d", user_id)
        return shift


async def end_shift(
    user_id: int,
    gross_earnings: float,
    distance_km: float,
    trips_count: int = 0,
    rent_cost: float = 0.0,
    notes: str = ""
) -> Optional[Shift]:
    """End active shift and calculate expenses."""
    async with session_factory() as session:
        # Get active shift
        result = await session.execute(
            select(Shift).where(
                and_(
                    Shift.user_id == user_id,
                    Shift.end_time.is_(None)
                )
            ).order_by(Shift.start_time.desc())
        )
        shift = result.scalar_one_or_none()

        if not shift:
            return None

        # Get user settings (create if not exists)
        settings_result = await session.execute(
            select(UserFinancialSettings).where(UserFinancialSettings.user_id == user_id)
        )
        settings = settings_result.scalar_one_or_none()

        if not settings:
            settings = UserFinancialSettings(user_id=user_id)
            session.add(settings)
            await session.flush()  # Ensure defaults are set

        # Update shift data
        shift.end_time = datetime.now()
        shift.gross_earnings = gross_earnings
        shift.distance_km = distance_km
        shift.trips_count = trips_count
        shift.notes = notes

        # Calculate expenses
        shift.fuel_cost = settings.calculate_fuel_cost(distance_km)
        shift.commission = settings.calculate_commission(gross_earnings)
        shift.rent_cost = rent_cost  # Use provided rent cost

        # Calculate net earnings
        total_expenses = shift.fuel_cost + shift.commission + shift.rent_cost + shift.other_expenses
        shift.net_earnings = gross_earnings - total_expenses

        await session.commit()
        await session.refresh(shift)

        logger.info("Ended shift for user %d: gross=%.2f, net=%.2f", user_id, gross_earnings, shift.net_earnings)
        return shift


async def get_shifts_by_period(user_id: int, days: int = 7) -> list[Shift]:
    """Get user's shifts for the last N days."""
    async with session_factory() as session:
        since = datetime.now() - timedelta(days=days)
        result = await session.execute(
            select(Shift).where(
                and_(
                    Shift.user_id == user_id,
                    Shift.start_time >= since,
                    Shift.end_time.isnot(None)
                )
            ).order_by(Shift.start_time.desc())
        )
        return list(result.scalars().all())


async def get_statistics(user_id: int, period: str = "week") -> dict:
    """
    Get financial statistics for a period.

    Args:
        user_id: Telegram user ID
        period: "day", "week", or "month"

    Returns:
        Dictionary with statistics
    """
    days_map = {"day": 1, "week": 7, "month": 30}
    days = days_map.get(period, 7)

    shifts = await get_shifts_by_period(user_id, days)

    if not shifts:
        return {
            "period": period,
            "shifts_count": 0,
            "total_hours": 0,
            "gross_earnings": 0,
            "net_earnings": 0,
            "total_distance": 0,
            "total_trips": 0,
            "avg_hourly_rate": 0,
            "expenses": {
                "fuel": 0,
                "commission": 0,
                "rent": 0,
                "other": 0,
                "total": 0,
            }
        }

    total_hours = sum(s.duration_hours for s in shifts)
    gross_earnings = sum(s.gross_earnings for s in shifts)
    net_earnings = sum(s.net_earnings for s in shifts)
    total_distance = sum(s.distance_km for s in shifts)
    total_trips = sum(s.trips_count for s in shifts)

    fuel_cost = sum(s.fuel_cost for s in shifts)
    commission = sum(s.commission for s in shifts)
    rent_cost = sum(s.rent_cost for s in shifts)
    other_expenses = sum(s.other_expenses for s in shifts)

    return {
        "period": period,
        "shifts_count": len(shifts),
        "total_hours": total_hours,
        "gross_earnings": gross_earnings,
        "net_earnings": net_earnings,
        "total_distance": total_distance,
        "total_trips": total_trips,
        "avg_hourly_rate": net_earnings / total_hours if total_hours > 0 else 0,
        "expenses": {
            "fuel": fuel_cost,
            "commission": commission,
            "rent": rent_cost,
            "other": other_expenses,
            "total": fuel_cost + commission + rent_cost + other_expenses,
        }
    }


async def update_settings(user_id: int, **kwargs) -> UserFinancialSettings:
    """Update user's financial settings."""
    async with session_factory() as session:
        result = await session.execute(
            select(UserFinancialSettings).where(UserFinancialSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = UserFinancialSettings(user_id=user_id)
            session.add(settings)

        # Handle tariff change specially (updates commission automatically)
        if 'tariff' in kwargs:
            settings.set_tariff(kwargs['tariff'])
            kwargs.pop('tariff')  # Remove from kwargs to avoid double-setting

        # Update other fields
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        await session.commit()
        await session.refresh(settings)
        return settings
