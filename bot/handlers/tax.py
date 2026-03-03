"""Tax calculator handler for self-employed drivers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.tax_calculator import TaxCalculator
from bot.services.financial import get_shifts_by_period
from bot.services.subscription import check_feature_access

router = Router()


@router.message(Command("tax"))
async def cmd_tax(message: Message) -> None:
    """Show tax calculator menu"""
    await show_tax_menu(message)


@router.callback_query(F.data == "menu_tax")
async def cb_tax_menu(callback: CallbackQuery) -> None:
    """Show tax calculator menu from callback"""
    await show_tax_menu(callback.message, callback)


async def show_tax_menu(message: Message, callback: CallbackQuery = None) -> None:
    """Display tax calculator main menu"""
    user_id = callback.from_user.id if callback else message.from_user.id

    # Check Elite subscription
    has_access = await check_feature_access(user_id, "tax_calculator")
    if not has_access:
        builder = InlineKeyboardBuilder()
        builder.button(text="⭐ Улучшить до Elite", callback_data="sub:upgrade")
        builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
        builder.adjust(1)

        text = (
            "🔒 <b>Калькулятор налогов доступен только в Elite подписке</b>\n\n"
            "С Elite подпиской вы получите:\n"
            "✅ Автоматический расчёт налогов для самозанятых\n"
            "✅ Расчёт по периодам (месяц, квартал, год)\n"
            "✅ Учёт налогового вычета НПД\n"
            "✅ Экспорт данных и карту заработка\n\n"
            "💎 Elite — 999₽/месяц"
        )

        if callback:
            await callback.message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
            await callback.answer()
        else:
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="📅 За месяц", callback_data="tax_calc_month")
    builder.button(text="📊 За квартал", callback_data="tax_calc_quarter")
    builder.button(text="📈 За год", callback_data="tax_calc_year")
    builder.button(text="ℹ️ О налоге НПД", callback_data="tax_info")
    builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
    builder.adjust(2, 1, 1, 1)

    text = (
        "💰 <b>Калькулятор налогов для самозанятых</b>\n\n"
        "Рассчитайте налог на профессиональный доход (НПД) "
        "на основе ваших смен.\n\n"
        "Выберите период для расчета:"
    )

    if callback:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
    else:
        await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("tax_calc_"))
async def cb_tax_calculate(callback: CallbackQuery) -> None:
    """Calculate tax for selected period"""
    period = callback.data.split("_")[2]  # month, quarter, year

    # Map period to days
    days_map = {"month": 30, "quarter": 90, "year": 365}
    period_names = {"month": "за месяц", "quarter": "за квартал", "year": "за год"}

    days = days_map[period]
    period_name = period_names[period]

    # Get user's shifts for the period
    shifts = await get_shifts_by_period(callback.from_user.id, days)

    if not shifts:
        text = f"📭 Нет данных о сменах {period_name}.\n\nДобавьте смены, чтобы рассчитать налог."
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Назад", callback_data="menu_tax")
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
        await callback.answer()
        return

    # Calculate total gross earnings
    total_income = sum(shift.gross_earnings for shift in shifts)

    # Show client type selection
    builder = InlineKeyboardBuilder()
    builder.button(text="👤 Физлица (4%)", callback_data=f"tax_result_{period}_individual_{total_income}")
    builder.button(text="🏢 Юрлица (6%)", callback_data=f"tax_result_{period}_legal_{total_income}")
    builder.button(text="🔙 Назад", callback_data="menu_tax")
    builder.adjust(2, 1)

    text = (
        f"📊 <b>Ваш доход {period_name}</b>\n\n"
        f"💰 Общий доход: {total_income:,.2f} ₽\n"
        f"🚕 Смен: {len(shifts)}\n\n"
        "Выберите тип клиентов:"
    )

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("tax_result_"))
async def cb_tax_result(callback: CallbackQuery) -> None:
    """Show tax calculation result"""
    parts = callback.data.split("_")
    period = parts[2]
    client_type = parts[3]
    income = float(parts[4])

    period_names = {"month": "за месяц", "quarter": "за квартал", "year": "за год"}
    period_name = period_names[period]

    # Calculate tax (assuming full deduction available and no prior income)
    calculator = TaxCalculator()
    result = calculator.calculate(income, client_type)

    text = calculator.format_calculation(result, period_name)

    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Другой период", callback_data="menu_tax")
    builder.button(text="ℹ️ О налоге НПД", callback_data="tax_info")
    builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
    builder.adjust(2, 1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "tax_info")
async def cb_tax_info(callback: CallbackQuery) -> None:
    """Show information about self-employed tax"""
    text = (
        "ℹ️ <b>Налог на профессиональный доход (НПД)</b>\n\n"
        "<b>Ставки налога:</b>\n"
        "• 4% — доход от физических лиц\n"
        "• 6% — доход от юридических лиц\n\n"
        "<b>Налоговый вычет:</b>\n"
        "Государство даёт вычет до 10,000 ₽, который снижает ставку:\n"
        "• С 4% до 3% (для физлиц)\n"
        "• С 6% до 4% (для юрлиц)\n\n"
        "<b>Годовой лимит:</b>\n"
        "Максимальный доход: 2,400,000 ₽ в год\n\n"
        "<b>Преимущества НПД:</b>\n"
        "✅ Низкие ставки налога\n"
        "✅ Не нужно сдавать отчётность\n"
        "✅ Легальная работа\n"
        "✅ Идёт пенсионный стаж\n"
        "✅ Можно работать без кассы\n\n"
        "<b>Пример расчёта:</b>\n"
        "Доход за месяц: 100,000 ₽ (от физлиц)\n"
        "• Без вычета: 100,000 × 4% = 4,000 ₽\n"
        "• С вычетом: 100,000 × 3% = 3,000 ₽\n"
        "💰 Экономия: 1,000 ₽"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="💰 Рассчитать налог", callback_data="menu_tax")
    builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()
