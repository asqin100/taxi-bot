"""Event management service."""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.event import Event
from bot.database.db import session_factory

logger = logging.getLogger(__name__)


async def create_event(
    name: str,
    zone_id: str,
    event_type: str,
    end_time: datetime,
) -> Event:
    """Create a new event."""
    async with session_factory() as session:
        event = Event(
            name=name,
            zone_id=zone_id,
            event_type=event_type,
            end_time=end_time,
            created_at=datetime.now(),
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        logger.info("Created event: %s at %s, ends at %s", name, zone_id, end_time)
        return event


async def get_upcoming_events(limit: int = 10) -> list[Event]:
    """Get upcoming events (not ended yet)."""
    async with session_factory() as session:
        stmt = (
            select(Event)
            .where(Event.end_time > datetime.now())
            .order_by(Event.end_time)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_events_for_pre_notification() -> list[Event]:
    """Get events that need pre-notification (20 min before end, not yet notified)."""
    now = datetime.now()
    pre_notify_time = now + timedelta(minutes=20)

    async with session_factory() as session:
        stmt = (
            select(Event)
            .where(
                Event.end_time <= pre_notify_time,
                Event.end_time > now,
                Event.pre_notified == False,
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_events_for_end_notification() -> list[Event]:
    """Get events that just ended (within last 5 min, not yet notified)."""
    now = datetime.now()
    five_min_ago = now - timedelta(minutes=5)

    async with session_factory() as session:
        stmt = (
            select(Event)
            .where(
                Event.end_time <= now,
                Event.end_time >= five_min_ago,
                Event.end_notified == False,
            )
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def mark_pre_notified(event_id: int):
    """Mark event as pre-notified."""
    async with session_factory() as session:
        stmt = select(Event).where(Event.id == event_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        if event:
            event.pre_notified = True
            await session.commit()
            logger.info("Marked event %d as pre-notified", event_id)


async def mark_end_notified(event_id: int):
    """Mark event as end-notified."""
    async with session_factory() as session:
        stmt = select(Event).where(Event.id == event_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        if event:
            event.end_notified = True
            await session.commit()
            logger.info("Marked event %d as end-notified", event_id)


async def delete_event(event_id: int) -> bool:
    """Delete an event."""
    async with session_factory() as session:
        stmt = select(Event).where(Event.id == event_id)
        result = await session.execute(stmt)
        event = result.scalar_one_or_none()
        if event:
            await session.delete(event)
            await session.commit()
            logger.info("Deleted event %d", event_id)
            return True
        return False
