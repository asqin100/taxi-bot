"""Challenge model - weekly challenges for gamification."""
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, String, DateTime, Boolean, Integer, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class ChallengeType(str, Enum):
    """Challenge types."""
    EARNINGS = "earnings"  # Earn X rubles this week
    SHIFTS = "shifts"  # Complete X shifts this week
    HOURS = "hours"  # Work X hours this week
    TRIPS = "trips"  # Complete X trips this week
    DISTANCE = "distance"  # Drive X km this week
    NIGHT_SHIFTS = "night_shifts"  # Complete X night shifts
    HIGH_RATE = "high_rate"  # Achieve X rub/hour rate


class UserChallenge(Base):
    """User's weekly challenge progress."""
    __tablename__ = "user_challenges"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    challenge_type: Mapped[str] = mapped_column(String(50))

    # Challenge details
    target: Mapped[float] = mapped_column(Float)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    reward_description: Mapped[str] = mapped_column(String(200))

    # Status
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Week tracking
    week_start: Mapped[datetime] = mapped_column(DateTime, index=True)
    week_end: Mapped[datetime] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target == 0:
            return 100.0
        return min(100.0, (self.progress / self.target) * 100)

    @property
    def is_active(self) -> bool:
        """Check if challenge is still active."""
        return datetime.now() < self.week_end and not self.is_completed


# Challenge templates
CHALLENGE_TEMPLATES = {
    ChallengeType.EARNINGS: {
        "name": "Недельный заработок",
        "description": "Заработайте {target}₽ за неделю",
        "emoji": "💰",
        "targets": [15000, 25000, 40000],  # Different difficulty levels
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
    ChallengeType.SHIFTS: {
        "name": "Активный водитель",
        "description": "Завершите {target} смен за неделю",
        "emoji": "🚕",
        "targets": [5, 10, 15],
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
    ChallengeType.HOURS: {
        "name": "Марафонец",
        "description": "Отработайте {target} часов за неделю",
        "emoji": "⏱",
        "targets": [30, 50, 70],
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
    ChallengeType.TRIPS: {
        "name": "Популярный водитель",
        "description": "Завершите {target} поездок за неделю",
        "emoji": "🎯",
        "targets": [50, 100, 150],
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
    ChallengeType.DISTANCE: {
        "name": "Дальнобойщик",
        "description": "Проедьте {target} км за неделю",
        "emoji": "🛣",
        "targets": [500, 1000, 1500],
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
    ChallengeType.NIGHT_SHIFTS: {
        "name": "Ночной волк",
        "description": "Завершите {target} ночных смен за неделю",
        "emoji": "🌙",
        "targets": [3, 5, 7],
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
    ChallengeType.HIGH_RATE: {
        "name": "Эффективность",
        "description": "Достигните ставки {target}₽/час",
        "emoji": "⚡",
        "targets": [800, 1000, 1200],
        "rewards": ["Бронзовый знак", "Серебряный знак", "Золотой знак"],
    },
}
