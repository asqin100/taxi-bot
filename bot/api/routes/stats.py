"""API route for statistics."""
from fastapi import APIRouter, Depends, Query

from bot.api.auth import get_current_user
from bot.api.schemas import StatsResponse
from bot.models.user import User
from bot.services.financial import get_statistics

router = APIRouter()


@router.get("/stats/summary", response_model=StatsResponse)
async def get_stats_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days for statistics"),
    current_user: User = Depends(get_current_user)
):
    """
    Get driver statistics summary for the specified period.

    - **days**: Number of days to analyze (1-90)

    Returns comprehensive statistics including:
    - Total shifts and hours worked
    - Gross and net earnings
    - Total distance and trips
    - Average hourly rate
    - Expense breakdown
    """
    # Map days to period string
    if days <= 1:
        period = "day"
    elif days <= 7:
        period = "week"
    else:
        period = "month"

    stats = await get_statistics(current_user.telegram_id, period)
    stats["period_days"] = days

    return StatsResponse(**stats)
