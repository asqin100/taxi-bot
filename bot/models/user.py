from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Float, String, DateTime, Integer, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    tariffs: Mapped[str] = mapped_column(String(128), default="econom")  # comma-separated
    preferred_tariff: Mapped[str] = mapped_column(String(20), default="econom")  # Primary tariff for alerts and recommendations
    zones: Mapped[str] = mapped_column(String(512), default="")  # comma-separated zone ids
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    surge_threshold: Mapped[float] = mapped_column(Float, default=1.5)

    # Event notification settings
    event_notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    event_types: Mapped[str] = mapped_column(String(128), default="concert,sport")  # comma-separated: concert,sport,theater,conference,other

    # Nightclub alerts
    nightclub_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Quiet hours settings
    quiet_hours_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    quiet_hours_start: Mapped[int] = mapped_column(Integer, default=22)  # Hour (0-23)
    quiet_hours_end: Mapped[int] = mapped_column(Integer, default=7)  # Hour (0-23)

    # Geolocation alerts
    geo_alerts_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    last_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    last_location_update: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    live_location_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Geo alerts daily limit tracking
    geo_alerts_sent_today: Mapped[int] = mapped_column(Integer, default=0)
    geo_alerts_reset_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Where to go daily limit tracking
    where_to_go_requests_today: Mapped[int] = mapped_column(Integer, default=0)
    where_to_go_reset_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Onboarding
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    # Referral system
    referral_code: Mapped[str | None] = mapped_column(String(16), unique=True, index=True)
    referrer_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    referral_balance: Mapped[float] = mapped_column(Float, default=0.0)

    # Export tracking
    last_export_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Ban system
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str | None] = mapped_column(String(256), nullable=True)
    banned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    referrer: Mapped["User"] = relationship("User", remote_side=[id], foreign_keys=[referrer_id], back_populates="referrals")
    referrals: Mapped[list["User"]] = relationship("User", back_populates="referrer", foreign_keys=[referrer_id])
    referral_earnings: Mapped[list["ReferralEarning"]] = relationship("ReferralEarning", foreign_keys="ReferralEarning.user_id", back_populates="user")
