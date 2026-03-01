"""Achievement model - gamification system for drivers."""
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, String, DateTime, Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class AchievementType(str, Enum):
    """Achievement types."""
    FIRST_SHIFT = "first_shift"
    NIGHT_OWL = "night_owl"  # 10 night shifts
    EARLY_BIRD = "early_bird"  # 10 morning shifts
    AIRPORT_HUNTER = "airport_hunter"  # Work near airports
    MARATHON = "marathon"  # 12+ hour shift
    MILLIONAIRE = "millionaire"  # 1M rubles earned
    WEEK_WARRIOR = "week_warrior"  # 7 days in a row
    SURGE_MASTER = "surge_master"  # Catch 10 high surges
    EFFICIENT = "efficient"  # High hourly rate
    CONSISTENT = "consistent"  # 30 shifts completed


class UserAchievement(Base):
    """User achievement progress and unlocks."""
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    achievement_type: Mapped[str] = mapped_column(String(50), index=True)

    # Progress tracking
    progress: Mapped[int] = mapped_column(Integer, default=0)
    target: Mapped[int] = mapped_column(Integer)
    is_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)

    # Unlock timestamp
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage."""
        if self.target == 0:
            return 100.0
        return min(100.0, (self.progress / self.target) * 100)


# Achievement definitions
ACHIEVEMENTS = {
    AchievementType.FIRST_SHIFT: {
        "name": "Первая смена",
        "description": "Завершите свою первую смену",
        "emoji": "🎉",
        "target": 1,
        "reward": "Начало пути!",
    },
    AchievementType.NIGHT_OWL: {
        "name": "Ночная сова",
        "description": "Завершите 10 ночных смен (22:00-06:00)",
        "emoji": "🦉",
        "target": 10,
        "reward": "Мастер ночных дорог",
    },
    AchievementType.EARLY_BIRD: {
        "name": "Ранняя пташка",
        "description": "Завершите 10 утренних смен (06:00-10:00)",
        "emoji": "🐦",
        "target": 10,
        "reward": "Покоритель утренних пробок",
    },
    AchievementType.AIRPORT_HUNTER: {
        "name": "Аэропортный охотник",
        "description": "Работайте возле аэропортов 20 раз",
        "emoji": "✈️",
        "target": 20,
        "reward": "Эксперт аэропортов",
    },
    AchievementType.MARATHON: {
        "name": "Марафонец",
        "description": "Завершите смену длительностью 12+ часов",
        "emoji": "🏃",
        "target": 1,
        "reward": "Железная выдержка",
    },
    AchievementType.MILLIONAIRE: {
        "name": "Миллионер",
        "description": "Заработайте 1 000 000 рублей",
        "emoji": "💰",
        "target": 1000000,
        "reward": "Финансовый успех!",
    },
    AchievementType.WEEK_WARRIOR: {
        "name": "Недельный воин",
        "description": "Работайте 7 дней подряд",
        "emoji": "⚔️",
        "target": 7,
        "reward": "Несгибаемая воля",
    },
    AchievementType.SURGE_MASTER: {
        "name": "Мастер коэффициентов",
        "description": "Поймайте 10 высоких коэффициентов (x2.0+)",
        "emoji": "🔥",
        "target": 10,
        "reward": "Охотник за кэфами",
    },
    AchievementType.EFFICIENT: {
        "name": "Эффективный",
        "description": "Достигните почасовой ставки 1500₽/час",
        "emoji": "⚡",
        "target": 1,
        "reward": "Мастер оптимизации",
    },
    AchievementType.CONSISTENT: {
        "name": "Постоянный",
        "description": "Завершите 30 смен",
        "emoji": "🎯",
        "target": 30,
        "reward": "Профессионал",
    },
}
