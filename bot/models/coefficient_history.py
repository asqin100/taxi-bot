"""Coefficient history model for storing surge data over time."""
from datetime import datetime

from sqlalchemy import String, DateTime, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class CoefficientHistory(Base):
    """Historical surge coefficient data for ML predictions."""
    __tablename__ = "coefficient_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    zone_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tariff: Mapped[str] = mapped_column(String(32), nullable=False)
    coefficient: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index('idx_zone_tariff_time', 'zone_id', 'tariff', 'timestamp'),
    )
