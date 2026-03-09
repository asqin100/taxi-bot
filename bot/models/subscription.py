"""Subscription model - user subscription tiers and limits."""
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, String, DateTime, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    FREE = "free"
    PRO = "pro"
    PREMIUM = "premium"
    ELITE = "elite"


class Subscription(Base):
    """User subscription information."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)

    # Subscription details
    tier: Mapped[str] = mapped_column(String(20), default=SubscriptionTier.FREE.value)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Subscription period
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Payment tracking
    last_payment_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    @property
    def is_expired(self) -> bool:
        """Check if subscription is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at

    @property
    def is_pro_or_higher(self) -> bool:
        """Check if user has Pro or Premium subscription."""
        return self.tier in [SubscriptionTier.PRO.value, SubscriptionTier.PREMIUM.value]

    @property
    def is_premium(self) -> bool:
        """Check if user has Premium subscription."""
        return self.tier == SubscriptionTier.PREMIUM.value

    @property
    def is_elite(self) -> bool:
        """Check if user has Elite subscription."""
        return self.tier == SubscriptionTier.ELITE.value

    @property
    def features(self) -> list[str]:
        """Get list of features for current tier."""
        from bot.models.subscription import SUBSCRIPTION_FEATURES
        return SUBSCRIPTION_FEATURES.get(self.tier, {}).get("features", [])


# Subscription limits and features
SUBSCRIPTION_FEATURES = {
    SubscriptionTier.FREE: {
        "name": "Бесплатный",
        "price": 0,
        "max_alerts": 3,
        "ai_advisor": False,
        "geo_alerts": False,
        "priority_notifications": False,
        "detailed_analytics": False,
        "business_tariff": False,
        "traffic": False,
        "features": [
            "✅ Базовый радар коэффициентов",
            "✅ Тарифы: Эконом, Комфорт",
            "✅ До 3 уведомлений",
            "✅ Топ-5 жирных точек",
            "⏱ Уведомления через 120 секунд",
        ]
    },
    SubscriptionTier.PRO: {
        "name": "Pro",
        "price": 299,
        "max_alerts": 999,  # unlimited
        "ai_advisor": True,
        "geo_alerts": True,
        "priority_notifications": False,
        "detailed_analytics": True,
        "business_tariff": True,
        "traffic": True,
        "features": [
            "✅ Все функции бесплатного",
            "✅ Доступ к тарифу Бизнес 🚕",
            "✅ Неограниченные уведомления",
            "⏱ Уведомления через 90 секунд",
            "✅ Прогноз пробок 🚦",
            "✅ AI-советник (5 вопросов/день)",
            "✅ Геоалерты (уведомления рядом с вами)",
            "✅ Детальная аналитика",
            "✅ Горячие точки (аэропорты, вокзалы)",
        ]
    },
    SubscriptionTier.PREMIUM: {
        "name": "Premium",
        "price": 499,
        "max_alerts": 999,
        "ai_advisor": True,
        "geo_alerts": True,
        "priority_notifications": True,
        "detailed_analytics": True,
        "business_tariff": True,
        "traffic": True,
        "features": [
            "✅ Все функции Pro",
            "⚡ Приоритет: уведомления через 60 секунд",
            "✅ AI-советник (20 вопросов/день)",
            "✅ Расширенная аналитика",
            "✅ Персональные рекомендации",
            "✅ Поддержка 24/7",
        ]
    },
    SubscriptionTier.ELITE: {
        "name": "Elite",
        "price": 999,
        "max_alerts": 999,
        "ai_advisor": True,
        "geo_alerts": True,
        "priority_notifications": True,
        "detailed_analytics": True,
        "business_tariff": True,
        "traffic": True,
        "csv_export": True,
        "heatmap": True,
        "tax_calculator": True,
        "api_access": True,
        "extended_stats": True,
        "features": [
            "✅ Все функции Premium",
            "🚀 Максимальный приоритет: уведомления мгновенно",
            "✅ Выгрузка смен для налоговой (безлимит)",
            "✅ Карта заработка: когда выгоднее работать",
            "✅ Статистика за месяц",
            "✅ Прогноз спроса на 24 часа вперёд",
            "✅ Автоматический расчёт налогов для самозанятых",
            "✅ Доступ к данным из других приложений",
        ]
    }
}
