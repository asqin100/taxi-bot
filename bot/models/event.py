from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(256))
    zone_id: Mapped[str] = mapped_column(String(64))  # Zone where event is happening
    event_type: Mapped[str] = mapped_column(String(64))  # concert, sport, conference, etc.
    end_time: Mapped[datetime] = mapped_column(DateTime)

    # Venue information for better notifications
    venue_name: Mapped[str | None] = mapped_column(String(256), nullable=True)  # Human-readable venue name
    venue_lat: Mapped[float | None] = mapped_column(Float, nullable=True)  # Venue latitude
    venue_lon: Mapped[float | None] = mapped_column(Float, nullable=True)  # Venue longitude

    # Alert tracking
    pre_notified: Mapped[bool] = mapped_column(Boolean, default=False)  # 20 min before alert sent
    end_notified: Mapped[bool] = mapped_column(Boolean, default=False)  # End alert sent

    created_at: Mapped[datetime] = mapped_column(DateTime)
