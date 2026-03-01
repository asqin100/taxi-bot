"""Shift model - tracks driver work shifts."""
from datetime import datetime

from sqlalchemy import BigInteger, String, DateTime, Float, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class Shift(Base):
    """Driver work shift with earnings and expenses."""
    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)  # telegram_id

    # Shift timing
    start_time: Mapped[datetime] = mapped_column(DateTime)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Earnings
    gross_earnings: Mapped[float] = mapped_column(Float, default=0.0)  # Total earnings before expenses

    # Trip data
    trips_count: Mapped[int] = mapped_column(Integer, default=0)
    distance_km: Mapped[float] = mapped_column(Float, default=0.0)

    # Expenses (calculated or manual)
    fuel_cost: Mapped[float] = mapped_column(Float, default=0.0)
    rent_cost: Mapped[float] = mapped_column(Float, default=0.0)
    commission: Mapped[float] = mapped_column(Float, default=0.0)
    other_expenses: Mapped[float] = mapped_column(Float, default=0.0)

    # Calculated fields
    net_earnings: Mapped[float] = mapped_column(Float, default=0.0)  # gross - all expenses

    # Notes
    notes: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    @property
    def duration_hours(self) -> float:
        """Calculate shift duration in hours."""
        if not self.end_time:
            return 0.0
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600

    @property
    def hourly_rate(self) -> float:
        """Calculate hourly earnings rate."""
        hours = self.duration_hours
        if hours < 0.01:  # Less than ~36 seconds
            return 0.0
        return self.net_earnings / hours
