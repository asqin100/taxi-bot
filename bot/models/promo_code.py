"""Promo code model for subscription discounts."""
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, DateTime, Boolean, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class PromoCode(Base):
    """Promo code for subscription activation or discount."""
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(primary_key=True)

    # Code details
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    # Promo type: "activation" (free subscription) or "discount" (price reduction)
    promo_type: Mapped[str] = mapped_column(String(20), default="activation")

    # For activation type
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True)  # pro, premium, elite
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # For discount type
    discount_type: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "percent" or "fixed"
    discount_value: Mapped[float | None] = mapped_column(Float, nullable=True)  # 20 for 20% or 100 for 100 RUB
    applicable_tiers: Mapped[str | None] = mapped_column(String(100), nullable=True)  # "pro,premium,elite"

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

    def get_applicable_tiers(self) -> list[str]:
        """Get list of tiers this discount applies to."""
        if not self.applicable_tiers:
            return []
        return [t.strip() for t in self.applicable_tiers.split(",")]

    def is_applicable_to_tier(self, tier: str) -> bool:
        """Check if discount applies to given tier."""
        if self.promo_type == "activation":
            return self.tier == tier
        return tier in self.get_applicable_tiers()

    def calculate_discount(self, original_price: float) -> float:
        """Calculate discount amount."""
        if self.promo_type != "discount":
            return 0.0

        if self.discount_type == "percent":
            return original_price * (self.discount_value / 100.0)
        elif self.discount_type == "fixed":
            return min(self.discount_value, original_price)
        return 0.0

    def get_final_price(self, original_price: float) -> float:
        """Get final price after discount."""
        discount = self.calculate_discount(original_price)
        return max(0.0, original_price - discount)


class PromoCodeUsage(Base):
    """Track promo code usage by users."""
    __tablename__ = "promo_code_usage"

    id: Mapped[int] = mapped_column(primary_key=True)

    promo_code_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)

    # Usage type
    promo_type: Mapped[str] = mapped_column(String(20))  # "activation" or "discount"

    # For activation type
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # For discount type
    discount_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    original_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    used_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
