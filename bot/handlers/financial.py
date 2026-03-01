"""Financial tracker handlers - shift management and statistics."""
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services import financial as fin_service
from bot.services.achievements import check_shift_achievements, format_achievement_unlock
from bot.services.message_manager import send_and_cleanup

router = Router()


class ShiftStates(StatesGroup):
    """States for shift end flow."""
    waiting_for_earnings = State()
    waiting_for_distance = State()
    waiting_for_trips = State()
    waiting_for_rent = State()
    waiting_for_notes = State()


class ExpenseStates(StatesGroup):
    """States for expense settings."""
    waiting_for_fuel_price = State()
    waiting_for_consumption = State()
    waiting_for_rent = State()
    waiting_for_commission = State()


class GoalStates(StatesGroup):
    """States for goal setting."""
    waiting_for_daily_goal = State()
    waiting_for_weekly_goal = State()
    waiting_for_monthly_goal = State()


@router.message(Command("shift_start"))
async def cmd_shift_start(message: Message):
    """Start a new shift."""
    user_id = message.from_user.id

    # Check if there's already an active shift
    active_shift = await fin_service.get_active_shift(user_id)

    if active_shift:
        # Make message.date timezone-naive to match database datetime
        current_time = message.date.replace(tzinfo=None)
        duration = (current_time - active_shift.start_time).total_seconds() / 3600
        await send_and_cleanup(
            message,
            f"⚠️ У вас уже есть активная смена!\n\n"
            f"Начало: {active_shift.start_time.strftime('%d.%m %H:%M')}\n"
            f"Длительность: {duration:.1f} ч\n\n"
            f"Используйте /shift_end для завершения."
        )
        return

    # Start new shift
    shift = await fin_service.start_shift(user_id)

    await send_and_cleanup(
        message,
        f"✅ <b>Смена начата!</b>\n\n"
        f"🕐 Время начала: {shift.start_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Удачной работы! 🚕\n"
        f"Используйте /shift_end когда закончите.",
        parse_mode="HTML"
    )


@router.message(Command("shift_end"))
async def cmd_shift_end(message: Message, state: FSMContext):
    """End current shift - start the flow."""
    user_id = message.from_user.id

    # Check if there's an active shift
    active_shift = await fin_service.get_active_shift(user_id)

    if not active_shift:
        await send_and_cleanup(
            message,
            "⚠️ У вас нет активной смены.\n\n"
            "Используйте /shift_start чтобы начать."
        )
        return

    # Make message.date timezone-naive to match database datetime
    current_time = message.date.replace(tzinfo=None)
    duration = (current_time - active_shift.start_time).total_seconds() / 3600

    await send_and_cleanup(
        message,
        f"📊 <b>Завершение смены</b>\n\n"
        f"Начало: {active_shift.start_time.strftime('%d.%m %H:%M')}\n"
        f"Длительность: {duration:.1f} ч\n\n"
        f"Введите заработок (руб):",
        parse_mode="HTML"
    )

    await state.set_state(ShiftStates.waiting_for_earnings)


@router.message(ShiftStates.waiting_for_earnings)
async def process_earnings(message: Message, state: FSMContext):
    """Process earnings input."""
    try:
        earnings = float(message.text.replace(",", ".").replace(" ", ""))
        if earnings < 0:
            raise ValueError("Negative earnings")

        await state.update_data(earnings=earnings)
        await send_and_cleanup(
            message,
            f"✅ Заработок: {earnings:.2f} руб\n\n"
            f"Введите пробег (км):"
        )
        await state.set_state(ShiftStates.waiting_for_distance)

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Введите число (например: 5000 или 5000.50)")


@router.message(ShiftStates.waiting_for_distance)
async def process_distance(message: Message, state: FSMContext):
    """Process distance input."""
    try:
        distance = float(message.text.replace(",", ".").replace(" ", ""))
        if distance < 0:
            raise ValueError("Negative distance")

        await state.update_data(distance=distance)
        await send_and_cleanup(
            message,
            f"✅ Пробег: {distance:.1f} км\n\n"
            f"Введите количество поездок (или 0):"
        )
        await state.set_state(ShiftStates.waiting_for_trips)

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Введите число (например: 150 или 150.5)")


@router.message(ShiftStates.waiting_for_trips)
async def process_trips(message: Message, state: FSMContext):
    """Process trips count input."""
    try:
        trips = int(message.text.strip())
        if trips < 0:
            raise ValueError("Negative trips")

        await state.update_data(trips=trips)
        await send_and_cleanup(
            message,
            f"✅ Поездок: {trips}\n\n"
            f"Введите стоимость аренды за эту смену (руб):\n"
            f"(или 0 если свой автомобиль)"
        )
        await state.set_state(ShiftStates.waiting_for_rent)

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Введите целое число (например: 25)")


@router.message(ShiftStates.waiting_for_rent)
async def process_rent(message: Message, state: FSMContext):
    """Process rent input."""
    try:
        rent = float(message.text.replace(",", ".").replace(" ", ""))
        if rent < 0:
            raise ValueError("Negative rent")

        await state.update_data(rent=rent)
        await send_and_cleanup(
            message,
            f"✅ Аренда: {rent:.2f} руб\n\n"
            f"Добавить заметки? (или отправьте '-' чтобы пропустить)"
        )
        await state.set_state(ShiftStates.waiting_for_notes)

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Введите число (например: 1500 или 0)")


@router.message(ShiftStates.waiting_for_notes)
async def process_notes(message: Message, state: FSMContext):
    """Process notes and finalize shift."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    notes = message.text.strip() if message.text.strip() != "-" else ""

    # Get all data
    data = await state.get_data()
    user_id = message.from_user.id

    # End shift
    shift = await fin_service.end_shift(
        user_id=user_id,
        gross_earnings=data["earnings"],
        distance_km=data["distance"],
        trips_count=data["trips"],
        rent_cost=data["rent"],
        notes=notes
    )

    if not shift:
        await send_and_cleanup(message, "❌ Ошибка: активная смена не найдена.")
        await state.clear()
        return

    # Check achievements
    unlocked_achievements = await check_shift_achievements(user_id, shift)

    # Check challenge progress
    from bot.services.challenges import update_challenge_progress, format_challenge_completion
    completed_challenge = await update_challenge_progress(user_id, shift)

    # Format result
    result_text = (
        f"✅ <b>Смена завершена!</b>\n\n"
        f"⏱ Длительность: {shift.duration_hours:.1f} ч\n"
        f"🚕 Поездок: {shift.trips_count}\n"
        f"📏 Пробег: {shift.distance_km:.1f} км\n\n"
        f"💰 <b>Финансы:</b>\n"
        f"Заработок: {shift.gross_earnings:.2f} руб\n\n"
        f"<b>Расходы:</b>\n"
        f"  Топливо: {shift.fuel_cost:.2f} руб\n"
        f"  Комиссия: {shift.commission:.2f} руб\n"
        f"  Аренда: {shift.rent_cost:.2f} руб\n"
        f"  Итого: {shift.fuel_cost + shift.commission + shift.rent_cost:.2f} руб\n\n"
        f"💵 <b>Чистый доход: {shift.net_earnings:.2f} руб</b>\n"
        f"📊 Ставка: {shift.hourly_rate:.2f} руб/ч"
    )

    if notes:
        result_text += f"\n\n📝 Заметки: {notes}"

    # Create keyboard with back button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
    ])

    await message.answer(result_text, parse_mode="HTML", reply_markup=keyboard)

    # Send achievement notifications
    if unlocked_achievements:
        for achievement in unlocked_achievements:
            achievement_text = format_achievement_unlock(achievement)
            achievement_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Все достижения", callback_data="menu:achievements")],
                [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
            ])
            await message.answer(achievement_text, parse_mode="HTML", reply_markup=achievement_keyboard)

    # Send challenge completion notification
    if completed_challenge:
        challenge_text = format_challenge_completion(completed_challenge)
        challenge_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Мой челлендж", callback_data="menu:challenge")],
            [InlineKeyboardButton(text="📊 Главное меню", callback_data="cmd:menu")]
        ])
        await message.answer(challenge_text, parse_mode="HTML", reply_markup=challenge_keyboard)

    await state.clear()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Show financial statistics."""
    user_id = message.from_user.id

    # Get statistics for different periods
    day_stats = await fin_service.get_statistics(user_id, "day")
    week_stats = await fin_service.get_statistics(user_id, "week")
    month_stats = await fin_service.get_statistics(user_id, "month")

    # Get settings for goals
    settings = await fin_service.get_or_create_settings(user_id)

    text = "📊 <b>Статистика заработка</b>\n\n"

    # Today
    text += f"<b>📅 Сегодня:</b>\n"
    if day_stats["shifts_count"] > 0:
        text += (
            f"Смен: {day_stats['shifts_count']}\n"
            f"Часов: {day_stats['total_hours']:.1f}\n"
            f"Чистый доход: {day_stats['net_earnings']:.2f} руб\n"
            f"Ставка: {day_stats['avg_hourly_rate']:.2f} руб/ч\n"
        )
        if settings.daily_goal > 0:
            progress = (day_stats['net_earnings'] / settings.daily_goal) * 100
            text += f"Цель: {progress:.0f}% ({day_stats['net_earnings']:.0f}/{settings.daily_goal:.0f})\n"
    else:
        text += "Нет данных\n"

    text += "\n"

    # Week
    text += f"<b>📅 Неделя:</b>\n"
    if week_stats["shifts_count"] > 0:
        text += (
            f"Смен: {week_stats['shifts_count']}\n"
            f"Часов: {week_stats['total_hours']:.1f}\n"
            f"Чистый доход: {week_stats['net_earnings']:.2f} руб\n"
            f"Ставка: {week_stats['avg_hourly_rate']:.2f} руб/ч\n"
        )
        if settings.weekly_goal > 0:
            progress = (week_stats['net_earnings'] / settings.weekly_goal) * 100
            text += f"Цель: {progress:.0f}% ({week_stats['net_earnings']:.0f}/{settings.weekly_goal:.0f})\n"
    else:
        text += "Нет данных\n"

    text += "\n"

    # Month
    text += f"<b>📅 Месяц:</b>\n"
    if month_stats["shifts_count"] > 0:
        text += (
            f"Смен: {month_stats['shifts_count']}\n"
            f"Часов: {month_stats['total_hours']:.1f}\n"
            f"Чистый доход: {month_stats['net_earnings']:.2f} руб\n"
            f"Ставка: {month_stats['avg_hourly_rate']:.2f} руб/ч\n"
        )
        if settings.monthly_goal > 0:
            progress = (month_stats['net_earnings'] / settings.monthly_goal) * 100
            text += f"Цель: {progress:.0f}% ({month_stats['net_earnings']:.0f}/{settings.monthly_goal:.0f})\n"
    else:
        text += "Нет данных\n"

    await send_and_cleanup(message, text, parse_mode="HTML")


@router.message(Command("expenses"))
async def cmd_expenses(message: Message):
    """Show and configure expense settings."""
    user_id = message.from_user.id
    settings = await fin_service.get_or_create_settings(user_id)

    text = (
        f"💸 <b>Настройки расходов</b>\n\n"
        f"🚗 Тариф: {settings.tariff_name}\n"
        f"💳 Комиссия: {settings.commission_percent:.1f}%\n\n"
        f"⛽ Цена топлива: {settings.fuel_price_per_liter:.2f} руб/л\n"
        f"📊 Расход: {settings.fuel_consumption_per_100km:.1f} л/100км\n"
        f"🚗 Аренда: {settings.rent_per_day:.2f} руб/день\n\n"
        f"Для изменения используйте команды:\n"
        f"/set_fuel &lt;цена&gt;\n"
        f"/set_consumption &lt;расход&gt;\n"
        f"/set_rent &lt;сумма&gt;\n"
        f"/set_commission &lt;процент&gt;\n\n"
        f"💡 Или используйте меню: 💰 Финансы → 🚗 Мой тариф"
    )

    await send_and_cleanup(message, text, parse_mode="HTML")


@router.message(Command("set_fuel"))
async def cmd_set_fuel(message: Message):
    """Set fuel price."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_fuel 55.5")
            return

        price = float(parts[1].replace(",", "."))
        if price <= 0:
            raise ValueError("Invalid price")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, fuel_price_per_liter=price)

        await send_and_cleanup(message, f"✅ Цена топлива установлена: {price:.2f} руб/л")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_fuel 55.5")


@router.message(Command("set_consumption"))
async def cmd_set_consumption(message: Message):
    """Set fuel consumption."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_consumption 8.5")
            return

        consumption = float(parts[1].replace(",", "."))
        if consumption <= 0:
            raise ValueError("Invalid consumption")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, fuel_consumption_per_100km=consumption)

        await send_and_cleanup(message, f"✅ Расход топлива установлен: {consumption:.1f} л/100км")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_consumption 8.5")


@router.message(Command("set_rent"))
async def cmd_set_rent(message: Message):
    """Set daily rent cost."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_rent 1500 (или 0 если свой автомобиль)")
            return

        rent = float(parts[1].replace(",", "."))
        if rent < 0:
            raise ValueError("Invalid rent")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, rent_per_day=rent)

        if rent == 0:
            await send_and_cleanup(message, "✅ Аренда отключена (свой автомобиль)")
        else:
            await send_and_cleanup(message, f"✅ Аренда установлена: {rent:.2f} руб/день")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_rent 1500")


@router.message(Command("set_commission"))
async def cmd_set_commission(message: Message):
    """Set commission percentage."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_commission 20")
            return

        commission = float(parts[1].replace(",", "."))
        if commission < 0 or commission > 100:
            raise ValueError("Invalid commission")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, commission_percent=commission)

        await send_and_cleanup(message, f"✅ Комиссия установлена: {commission:.1f}%")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_commission 20")


@router.message(Command("goal"))
async def cmd_goal(message: Message):
    """Show and set financial goals."""
    user_id = message.from_user.id
    settings = await fin_service.get_or_create_settings(user_id)

    text = (
        f"🎯 <b>Финансовые цели</b>\n\n"
        f"📅 День: {settings.daily_goal:.0f} руб\n"
        f"📅 Неделя: {settings.weekly_goal:.0f} руб\n"
        f"📅 Месяц: {settings.monthly_goal:.0f} руб\n\n"
        f"Для изменения используйте:\n"
        f"/set_daily_goal &lt;сумма&gt;\n"
        f"/set_weekly_goal &lt;сумма&gt;\n"
        f"/set_monthly_goal &lt;сумма&gt;"
    )

    await send_and_cleanup(message, text, parse_mode="HTML")


@router.message(Command("set_daily_goal"))
async def cmd_set_daily_goal(message: Message):
    """Set daily earnings goal."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_daily_goal 5000")
            return

        goal = float(parts[1].replace(",", "."))
        if goal < 0:
            raise ValueError("Invalid goal")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, daily_goal=goal)

        await send_and_cleanup(message, f"✅ Дневная цель установлена: {goal:.0f} руб")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_daily_goal 5000")


@router.message(Command("set_weekly_goal"))
async def cmd_set_weekly_goal(message: Message):
    """Set weekly earnings goal."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_weekly_goal 30000")
            return

        goal = float(parts[1].replace(",", "."))
        if goal < 0:
            raise ValueError("Invalid goal")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, weekly_goal=goal)

        await send_and_cleanup(message, f"✅ Недельная цель установлена: {goal:.0f} руб")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_weekly_goal 30000")


@router.message(Command("set_monthly_goal"))
async def cmd_set_monthly_goal(message: Message):
    """Set monthly earnings goal."""
    try:
        parts = message.text.split(maxsplit=1)
        if len(parts) < 2:
            await send_and_cleanup(message, "Использование: /set_monthly_goal 120000")
            return

        goal = float(parts[1].replace(",", "."))
        if goal < 0:
            raise ValueError("Invalid goal")

        user_id = message.from_user.id
        await fin_service.update_settings(user_id, monthly_goal=goal)

        await send_and_cleanup(message, f"✅ Месячная цель установлена: {goal:.0f} руб")

    except ValueError:
        await send_and_cleanup(message, "❌ Неверный формат. Пример: /set_monthly_goal 120000")
