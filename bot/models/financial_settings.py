"""User financial settings model."""
from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.db import Base


# Tariff commission rates (typical values)
TARIFF_COMMISSIONS = {
    "econom": 18.0,
    "comfort": 21.0,
    "comfort_plus": 23.0,
    "business": 26.0,
}

TARIFF_NAMES = {
    "econom": "🚗 Эконом",
    "comfort": "🚙 Комфорт",
    "comfort_plus": "🚙+ Комфорт+",
    "business": "🚕 Бизнес",
}


class UserFinancialSettings(Base):
    """User's financial settings for automatic expense calculation."""
    __tablename__ = "user_financial_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)  # telegram_id

    # Tariff selection
    tariff: Mapped[str] = mapped_column(String(32), default="econom")  # econom, comfort, comfort_plus, business

    # Expense settings
    fuel_price_per_liter: Mapped[float] = mapped_column(Float, default=55.0)  # руб/литр
    fuel_consumption_per_100km: Mapped[float] = mapped_column(Float, default=8.0)  # литров/100км
    rent_per_day: Mapped[float] = mapped_column(Float, default=0.0)  # руб/день (0 = own car)
    commission_percent: Mapped[float] = mapped_column(Float, default=18.0)  # % от заработка

    # Goals
    daily_goal: Mapped[float] = mapped_column(Float, default=0.0)  # руб/день
    weekly_goal: Mapped[float] = mapped_column(Float, default=0.0)  # руб/неделя
    monthly_goal: Mapped[float] = mapped_column(Float, default=0.0)  # руб/месяц

    def calculate_fuel_cost(self, distance_km: float) -> float:
        """Calculate fuel cost for given distance."""
        liters = (distance_km / 100) * self.fuel_consumption_per_100km
        return liters * self.fuel_price_per_liter

    def calculate_commission(self, gross_earnings: float) -> float:
        """Calculate commission from gross earnings."""
        return gross_earnings * (self.commission_percent / 100)

    def set_tariff(self, tariff: str):
        """Set tariff and update commission accordingly."""
        if tariff in TARIFF_COMMISSIONS:
            self.tariff = tariff
            self.commission_percent = TARIFF_COMMISSIONS[tariff]

    @property
    def tariff_name(self) -> str:
        """Get human-readable tariff name."""
        return TARIFF_NAMES.get(self.tariff, self.tariff)
