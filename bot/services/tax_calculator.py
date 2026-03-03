"""
Tax calculator for self-employed (самозанятые) in Russia.

Tax rates:
- 4% for income from individuals (физлица)
- 6% for income from legal entities (юрлица)

Annual income limit: 2,400,000 RUB
Tax deduction: up to 10,000 RUB (reduces rate by 1%)
"""

from dataclasses import dataclass
from typing import Literal


@dataclass
class TaxCalculation:
    """Result of tax calculation"""
    income: float
    client_type: Literal["individual", "legal"]
    base_rate: float
    deduction_available: float
    deduction_used: float
    effective_rate: float
    tax_amount: float
    net_income: float
    remaining_limit: float


class TaxCalculator:
    """Calculator for self-employed taxes"""

    # Constants
    RATE_INDIVIDUAL = 4.0  # 4% for individuals
    RATE_LEGAL = 6.0  # 6% for legal entities
    ANNUAL_LIMIT = 2_400_000.0  # Annual income limit in RUB
    MAX_DEDUCTION = 10_000.0  # Maximum tax deduction in RUB
    DEDUCTION_PERCENT = 1.0  # Deduction reduces rate by 1%

    def __init__(self, deduction_remaining: float = MAX_DEDUCTION, annual_income: float = 0.0):
        """
        Initialize calculator.

        Args:
            deduction_remaining: Remaining tax deduction amount (default: full 10,000 RUB)
            annual_income: Current annual income (default: 0)
        """
        self.deduction_remaining = min(deduction_remaining, self.MAX_DEDUCTION)
        self.annual_income = annual_income

    def calculate(
        self,
        income: float,
        client_type: Literal["individual", "legal"] = "individual"
    ) -> TaxCalculation:
        """
        Calculate tax for given income.

        Args:
            income: Income amount in RUB
            client_type: Type of client ("individual" or "legal")

        Returns:
            TaxCalculation with detailed breakdown
        """
        # Determine base rate
        base_rate = self.RATE_INDIVIDUAL if client_type == "individual" else self.RATE_LEGAL

        # Calculate tax with deduction
        tax_without_deduction = income * base_rate / 100

        # Apply deduction (reduces tax by 1% of income, up to remaining deduction)
        deduction_amount = min(
            income * self.DEDUCTION_PERCENT / 100,
            self.deduction_remaining
        )

        tax_amount = tax_without_deduction - deduction_amount
        effective_rate = (tax_amount / income * 100) if income > 0 else 0

        # Calculate remaining annual limit
        remaining_limit = max(0, self.ANNUAL_LIMIT - self.annual_income - income)

        return TaxCalculation(
            income=income,
            client_type=client_type,
            base_rate=base_rate,
            deduction_available=self.deduction_remaining,
            deduction_used=deduction_amount,
            effective_rate=effective_rate,
            tax_amount=tax_amount,
            net_income=income - tax_amount,
            remaining_limit=remaining_limit
        )

    def calculate_period(
        self,
        monthly_income: float,
        months: int,
        client_type: Literal["individual", "legal"] = "individual"
    ) -> TaxCalculation:
        """
        Calculate tax for a period (month/quarter/year).

        Args:
            monthly_income: Average monthly income in RUB
            months: Number of months (1 for month, 3 for quarter, 12 for year)
            client_type: Type of client ("individual" or "legal")

        Returns:
            TaxCalculation for the period
        """
        total_income = monthly_income * months
        return self.calculate(total_income, client_type)

    @staticmethod
    def format_calculation(calc: TaxCalculation, period_name: str = "") -> str:
        """
        Format calculation result as text.

        Args:
            calc: TaxCalculation result
            period_name: Name of period (e.g., "за месяц", "за квартал")

        Returns:
            Formatted text
        """
        client_type_ru = "физлица" if calc.client_type == "individual" else "юрлица"
        period_suffix = f" {period_name}" if period_name else ""

        text = f"💰 <b>Расчет налога{period_suffix}</b>\n\n"
        text += f"📊 Доход: {calc.income:,.2f} ₽\n"
        text += f"👤 Тип клиента: {client_type_ru}\n"
        text += f"📈 Базовая ставка: {calc.base_rate}%\n\n"

        if calc.deduction_used > 0:
            text += f"🎁 <b>Налоговый вычет:</b>\n"
            text += f"   Доступно: {calc.deduction_available:,.2f} ₽\n"
            text += f"   Использовано: {calc.deduction_used:,.2f} ₽\n"
            text += f"   Эффективная ставка: {calc.effective_rate:.2f}%\n\n"

        text += f"💸 <b>Налог к уплате: {calc.tax_amount:,.2f} ₽</b>\n"
        text += f"✅ Чистый доход: {calc.net_income:,.2f} ₽\n\n"

        # Show limit warning if approaching
        if calc.remaining_limit < 500_000:
            text += f"⚠️ Остаток лимита: {calc.remaining_limit:,.2f} ₽\n"
        else:
            text += f"📊 Остаток лимита: {calc.remaining_limit:,.2f} ₽\n"

        if calc.remaining_limit <= 0:
            text += "\n🚫 <b>Превышен годовой лимит!</b> Необходимо перейти на другую систему налогообложения."

        return text
