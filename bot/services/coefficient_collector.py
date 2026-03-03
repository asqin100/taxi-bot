"""Service for collecting and storing historical coefficient data."""
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import AsyncSessionLocal
from bot.models.coefficient_history import CoefficientHistory
from bot.services.yandex_api import fetch_all_coefficients

logger = logging.getLogger(__name__)


async def collect_and_store_coefficients() -> int:
    """
    Fetch current coefficients and store them in the database.

    Returns:
        Number of coefficient records stored
    """
    try:
        # Fetch current coefficients
        surge_data = await fetch_all_coefficients()

        if not surge_data:
            logger.warning("No coefficient data fetched")
            return 0

        # Store in database
        async with AsyncSessionLocal() as session:
            stored_count = 0
            timestamp = datetime.utcnow()

            for data in surge_data:
                history = CoefficientHistory(
                    zone_id=data.zone_id,
                    tariff=data.tariff,
                    coefficient=data.coefficient,
                    timestamp=timestamp
                )
                session.add(history)
                stored_count += 1

            await session.commit()
            logger.info(f"Stored {stored_count} coefficient records")
            return stored_count

    except Exception as e:
        logger.error(f"Error collecting coefficients: {e}")
        return 0


async def get_historical_data(
    session: AsyncSession,
    zone_id: str | None = None,
    tariff: str | None = None,
    days: int = 60
) -> list[CoefficientHistory]:
    """
    Retrieve historical coefficient data.

    Args:
        session: Database session
        zone_id: Filter by zone (optional)
        tariff: Filter by tariff (optional)
        days: Number of days to look back

    Returns:
        List of CoefficientHistory records
    """
    from datetime import timedelta

    date_from = datetime.utcnow() - timedelta(days=days)

    query = select(CoefficientHistory).where(
        CoefficientHistory.timestamp >= date_from
    )

    if zone_id:
        query = query.where(CoefficientHistory.zone_id == zone_id)

    if tariff:
        query = query.where(CoefficientHistory.tariff == tariff)

    query = query.order_by(CoefficientHistory.timestamp.asc())

    result = await session.execute(query)
    return list(result.scalars().all())


async def get_data_coverage() -> dict:
    """
    Get statistics about historical data coverage.

    Returns:
        Dictionary with coverage statistics
    """
    async with AsyncSessionLocal() as session:
        # Count total records
        result = await session.execute(
            select(CoefficientHistory)
        )
        all_records = result.scalars().all()

        if not all_records:
            return {
                "total_records": 0,
                "zones": 0,
                "tariffs": 0,
                "oldest_record": None,
                "newest_record": None,
                "days_covered": 0
            }

        zones = set(r.zone_id for r in all_records)
        tariffs = set(r.tariff for r in all_records)
        timestamps = [r.timestamp for r in all_records]

        oldest = min(timestamps)
        newest = max(timestamps)
        days_covered = (newest - oldest).days

        return {
            "total_records": len(all_records),
            "zones": len(zones),
            "tariffs": len(tariffs),
            "oldest_record": oldest,
            "newest_record": newest,
            "days_covered": days_covered
        }
