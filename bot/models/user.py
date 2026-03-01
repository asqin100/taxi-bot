from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Float, String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    tariffs: Mapped[str] = mapped_column(String(128), default="econom")  # comma-separated
    zones: Mapped[str] = mapped_column(String(512), default="")  # comma-separated zone ids
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    surge_threshold: Mapped[float] = mapped_column(Float, default=1.5)

    # Event notification settings
    event_notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    event_types: Mapped[str] = mapped_column(String(128), default="concert,sport")  # comma-separated: concert,sport,theater,conference,other

    # Quiet hours settings
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[int] = mapped_column(Integer, default=22)  # Hour (0-23)
    quiet_hours_end: Mapped[int] = mapped_column(Integer, default=7)  # Hour (0-23)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
