"""Event management service."""
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.event import Event
from bot.database.db import session_factory
from bot.utils.timezone import now as get_moscow_now

logger = logging.getLogger(__name__)


async def create_event(
    name: str,
    zone_id: str,
    event_type: str,
    end_time: datetime,
    venue_name: str = None,
    venue_lat: float = None,
    venue_lon: float = None,
) -> Event:
    """Create a new event."""
    async with session_factory() as session:
        event = Event(
            name=name,
            zone_id=zone_id,
            event_type=event_type,
            end_time=end_time,
            venue_name=venue_name,
            venue_lat=venue_lat,
            venue_lon=venue_lon,
            created_at=get_moscow_now(),
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        logger.info("Created event: %s at %s (venue: %s), ends at %s", name, zone_id, venue_name or "unknown", end_time)
        return event


async def get_upcoming_events(limit: int = 10) -> list[Event]:
    """Get upcoming events (not ended yet)."""
    async with session_factory() as session:
        stmt = (
            select(Event)
            .where(Event.end_time > get_moscow_now())
            .order_by(Event.end_time)
            .limit(limit)
        )
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def get_events_for_pre_notification() -> list[Event]:
    """Get events that need pre-notification (20 min before end, not yet notified)."""
    now = get_moscow_now()
    pre_notify_time = now + timedelta(minutes=20)

    logger.debug("Looking for pre-notifications: now=%s, pre_notify_time=%s", now, pre_notify_time)

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
        events = list(result.scalars().all())

        logger.debug("Pre-notification query found %d events", len(events))
        for event in events:
            logger.debug("  - %s (ends at %s, pre_notified=%s)", event.name, event.end_time, event.pre_notified)

        return events


async def get_events_for_end_notification() -> list[Event]:
    """Get events that just ended (within last 5 min, not yet notified)."""
    now = get_moscow_now()
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
