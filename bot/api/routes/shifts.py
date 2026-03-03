"""API route for shift export."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, and_

from bot.api.auth import get_current_user
from bot.api.schemas import ShiftExportResponse, ShiftResponse
from bot.database.db import session_factory
from bot.models.user import User
from bot.models.shift import Shift

router = APIRouter()


@router.get("/shifts/export", response_model=ShiftExportResponse)
async def export_shifts(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to export"),
    status: Optional[str] = Query(default=None, description="Filter by status: active, completed, or all"),
    current_user: User = Depends(get_current_user)
):
    """
    Export driver shifts data for the specified period.

    - **days**: Number of days to look back (1-90)
    - **status**: Filter by shift status (active, completed, or all)

    Returns detailed shift information including earnings, expenses, and trip data.
    """
    date_from = datetime.now() - timedelta(days=days)

    async with session_factory() as session:
        # Build query
        query = select(Shift).where(
            Shift.user_id == current_user.telegram_id,
            Shift.start_time >= date_from
        )

        if status == "active":
            query = query.where(Shift.end_time.is_(None))
        elif status == "completed":
            query = query.where(Shift.end_time.isnot(None))

        query = query.order_by(Shift.start_time.desc())

        result = await session.execute(query)
        shifts = result.scalars().all()

    # Calculate statistics
    completed_shifts = [s for s in shifts if s.end_time is not None]
    active_shifts = [s for s in shifts if s.end_time is None]
    total_gross = sum(s.gross_earnings for s in completed_shifts)
    total_net = sum(s.net_earnings for s in completed_shifts)

    # Convert to response models
    shift_responses = [
        ShiftResponse(
            id=s.id,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_hours=s.duration_hours,
            gross_earnings=s.gross_earnings,
            net_earnings=s.net_earnings,
            trips_count=s.trips_count,
            distance_km=s.distance_km,
            fuel_cost=s.fuel_cost,
            commission=s.commission,
            rent_cost=s.rent_cost,
            other_expenses=s.other_expenses,
            notes=s.notes
        )
        for s in shifts
    ]

    return ShiftExportResponse(
        total_shifts=len(shifts),
        completed_shifts=len(completed_shifts),
        active_shifts=len(active_shifts),
        total_gross=total_gross,
        total_net=total_net,
        shifts=shift_responses,
        period_start=date_from,
        period_end=datetime.now()
    )
