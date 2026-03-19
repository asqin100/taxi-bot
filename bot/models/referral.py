"""Referral system models."""
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.database.db import Base


class EarningType(str, PyEnum):
    """Types of referral earnings."""
    LEVEL_1 = "level_1"  # 30% from direct referral
    LEVEL_2 = "level_2"  # 10% from second level
    FIRST_SUBSCRIPTION_BONUS = "first_subscription_bonus"  # +100₽ bonus
    MILESTONE_5 = "milestone_5"  # 5 referrals → +200₽
    MILESTONE_10 = "milestone_10"  # 10 referrals → +500₽
    MILESTONE_25 = "milestone_25"  # 25 referrals → +1500₽
    MILESTONE_50 = "milestone_50"  # 50 referrals → +5000₽
    GAME_EARNING = "game_earning"  # Earnings from playing the game
    WITHDRAWAL = "withdrawal"  # Withdrawal from balance (negative amount)


class ReferralEarning(Base):
    """History of referral earnings."""
    __tablename__ = "referral_earnings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)  # Amount earned in rubles
    earning_type: Mapped[str] = mapped_column(SQLEnum(EarningType), nullable=False)
    from_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)  # Who triggered this earning
    subscription_tier: Mapped[str | None] = mapped_column(String(20), nullable=True)  # pro/premium if from subscription
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], back_populates="referral_earnings")
    from_user: Mapped["User"] = relationship("User", foreign_keys=[from_user_id])

    def __repr__(self):
        return f"<ReferralEarning(user_id={self.user_id}, amount={self.amount}, type={self.earning_type})>"
