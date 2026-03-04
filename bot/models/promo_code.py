"""Promo code model for subscription discounts."""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class PromoCode(Base):
    """Promo code for subscription activation."""
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Code details
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    tier: Mapped[str] = mapped_column(String(20))  # pro, premium, elite
    duration_days: Mapped[int] = mapped_column(Integer)

    # Usage limits
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = unlimited
    current_uses: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Validity period
    valid_from: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Metadata
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # admin user_id
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def is_valid(self) -> bool:
        """Check if promo code is valid."""
        if not self.is_active:
            return False

        now = datetime.now()

        # Check validity period
        if now < self.valid_from:
            return False

        if self.valid_until and now > self.valid_until:
            return False

        # Check usage limit
        if self.max_uses is not None and self.current_uses >= self.max_uses:
            return False

        return True

    @property
    def uses_remaining(self) -> int | None:
        """Get remaining uses (None if unlimited)."""
        if self.max_uses is None:
            return None
        return max(0, self.max_uses - self.current_uses)


class PromoCodeUsage(Base):
    """Track promo code usage by users."""
    __tablename__ = "promo_code_usage"

    id: Mapped[int] = mapped_column(primary_key=True)

    promo_code_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    # What was granted
    tier: Mapped[str] = mapped_column(String(20))
    duration_days: Mapped[int] = mapped_column(Integer)

    used_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
