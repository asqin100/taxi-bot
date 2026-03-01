"""Menu navigation handlers."""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.inline import financial_menu_keyboard, traffic_menu_keyboard, search_menu_keyboard, main_menu_keyboard
from bot.services import financial as fin_service
from bot.services import traffic as traffic_service
from bot.services.yandex_api import get_cached_coefficients
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.callback_query(F.data == "menu:financial")
async def cb_financial_menu(callback: CallbackQuery):
    """Show financial tracker menu."""
    user_id = callback.from_user.id

    # Check if user has active shift
    active_shift = await fin_service.get_active_shift(user_id)
    has_active = active_shift is not None

    await callback.message.edit_text(
        "💰 <b>Финансовый трекер</b>\n\n"
        "Управляйте сменами, отслеживайте расходы и достигайте целей.",
        parse_mode="HTML",
        reply_markup=financial_menu_keyboard(has_active)
    )
    await callback.answer()


@router.callback_query(F.data == "menu:traffic")
async def cb_traffic_menu(callback: CallbackQuery):
    """Show traffic menu."""
    await callback.message.edit_text(
        "🚦 <b>Дорожная обстановка</b>\n\n"
        "Проверьте текущую ситуацию на дорогах Москвы.",
        parse_mode="HTML",
        reply_markup=traffic_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "menu:search")
async def cb_search_menu(callback: CallbackQuery):
    """Show search menu."""
    await callback.message.edit_text(
        "🔍 <b>Поиск по адресу</b>\n\n"
        "Узнайте коэффициенты для любого адреса в Москве.\n\n"
        "<b>Как использовать:</b>\n"
        "Отправьте команду:\n"
        "<code>/search Красная площадь</code>\n"
        "<code>/search м. Тверская</code>\n"
        "<code>/search Шереметьево</code>",
        parse_mode="HTML",
        reply_markup=search_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "search:help")
async def cb_search_help(callback: CallbackQuery):
    """Show search help."""
    await callback.message.edit_text(
        "🔍 <b>Поиск коэффициента по адресу</b>\n\n"
        "<b>Примеры использования:</b>\n\n"
        "📍 По адресу:\n"
        "<code>/search Красная площадь</code>\n"
        "<code>/search Тверская улица 15</code>\n\n"
        "🚇 По метро:\n"
        "<code>/search м. Тверская</code>\n"
        "<code>/search метро Маяковская</code>\n\n"
        "✈️ По аэропорту:\n"
        "<code>/search Шереметьево</code>\n"
        "<code>/search Внуково</code>\n\n"
        "Бот найдёт ближайшую зону и покажет текущие коэффициенты.",
        parse_mode="HTML",
        reply_markup=search_menu_keyboard()
    )
    await callback.answer()


# Financial menu actions
@router.callback_query(F.data == "financial:shift_start")
async def cb_shift_start(callback: CallbackQuery):
    """Start shift from menu."""
    user_id = callback.from_user.id

    # Check if there's already an active shift
    active_shift = await fin_service.get_active_shift(user_id)

    if active_shift:
        await callback.answer("⚠️ У вас уже есть активная смена!", show_alert=True)
        return

    # Start new shift
    shift = await fin_service.start_shift(user_id)

    await callback.message.edit_text(
        f"✅ <b>Смена начата!</b>\n\n"
        f"🕐 Время начала: {shift.start_time.strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Удачной работы! 🚕",
        parse_mode="HTML",
        reply_markup=financial_menu_keyboard(has_active_shift=True)
    )
    await callback.answer()


@router.callback_query(F.data == "financial:shift_end")
async def cb_shift_end(callback: CallbackQuery, state: FSMContext):
    """End shift from menu - start FSM flow."""
    from bot.handlers.financial import ShiftStates

    user_id = callback.from_user.id

    # Check if there's an active shift
    active_shift = await fin_service.get_active_shift(user_id)

    if not active_shift:
        await callback.answer("⚠️ У вас нет активной смены!", show_alert=True)
        return

    # Calculate duration
    from datetime import datetime
    current_time = datetime.now()
    duration = (current_time - active_shift.start_time).total_seconds() / 3600

    await callback.message.edit_text(
        f"📊 <b>Завершение смены</b>\n\n"
        f"Начало: {active_shift.start_time.strftime('%d.%m %H:%M')}\n"
        f"Длительность: {duration:.1f} ч\n\n"
        f"Введите заработок (руб):",
        parse_mode="HTML"
    )

    await state.set_state(ShiftStates.waiting_for_earnings)
    await callback.answer()


@router.callback_query(F.data == "financial:stats")
async def cb_stats(callback: CallbackQuery):
    """Show statistics from menu."""
    user_id = callback.from_user.id

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
        )
        if settings.weekly_goal > 0:
            progress = (week_stats['net_earnings'] / settings.weekly_goal) * 100
            text += f"Цель: {progress:.0f}%\n"
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
        )
        if settings.monthly_goal > 0:
            progress = (month_stats['net_earnings'] / settings.monthly_goal) * 100
            text += f"Цель: {progress:.0f}%\n"
    else:
        text += "Нет данных\n"

    # Check for active shift
    active_shift = await fin_service.get_active_shift(user_id)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=financial_menu_keyboard(has_active_shift=active_shift is not None)
    )
    await callback.answer()


@router.callback_query(F.data == "financial:expenses")
async def cb_expenses(callback: CallbackQuery):
    """Show expenses settings from menu."""
    user_id = callback.from_user.id
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
        f"💡 Или измените тариф через кнопку \"🚗 Мой тариф\""
    )

    # Check for active shift
    active_shift = await fin_service.get_active_shift(user_id)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=financial_menu_keyboard(has_active_shift=active_shift is not None)
    )
    await callback.answer()


@router.callback_query(F.data == "financial:goals")
async def cb_goals(callback: CallbackQuery):
    """Show goals from menu."""
    user_id = callback.from_user.id
    settings = await fin_service.get_or_create_settings(user_id)

    text = (
        f"🎯 <b>Финансовые цели</b>\n\n"
        f"📅 День: {settings.daily_goal:.0f} руб\n"
        f"📅 Неделя: {settings.weekly_goal:.0f} руб\n"
        f"📅 Месяц: {settings.monthly_goal:.0f} руб\n\n"
        f"Для изменения используйте команды:\n"
        f"/set_daily_goal &lt;сумма&gt;\n"
        f"/set_weekly_goal &lt;сумма&gt;\n"
        f"/set_monthly_goal &lt;сумма&gt;"
    )

    # Check for active shift
    active_shift = await fin_service.get_active_shift(user_id)

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=financial_menu_keyboard(has_active_shift=active_shift is not None)
    )
    await callback.answer()


@router.callback_query(F.data == "financial:tariff")
async def cb_tariff_menu(callback: CallbackQuery):
    """Show tariff selection menu."""
    from bot.keyboards.inline import tariff_selection_keyboard

    user_id = callback.from_user.id
    settings = await fin_service.get_or_create_settings(user_id)

    await callback.message.edit_text(
        f"🚗 <b>Выбор тарифа</b>\n\n"
        f"Текущий тариф: {settings.tariff_name}\n"
        f"Комиссия: {settings.commission_percent:.1f}%\n\n"
        f"Выберите тариф, на котором вы работаете.\n"
        f"Комиссия будет установлена автоматически.",
        parse_mode="HTML",
        reply_markup=tariff_selection_keyboard(settings.tariff)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tariff_select:"))
async def cb_tariff_select(callback: CallbackQuery):
    """Handle tariff selection."""
    from bot.keyboards.inline import tariff_selection_keyboard

    tariff = callback.data.split(":")[1]
    user_id = callback.from_user.id

    # Update tariff and commission
    await fin_service.update_settings(user_id, tariff=tariff)

    # Get updated settings
    settings = await fin_service.get_or_create_settings(user_id)

    await callback.message.edit_text(
        f"✅ <b>Тариф обновлён!</b>\n\n"
        f"Тариф: {settings.tariff_name}\n"
        f"Комиссия: {settings.commission_percent:.1f}%\n\n"
        f"Комиссия будет автоматически учитываться при расчёте смен.\n\n"
        f"💡 Если у вас особые условия, вы можете изменить комиссию вручную:\n"
        f"/set_commission <процент>",
        parse_mode="HTML",
        reply_markup=tariff_selection_keyboard(settings.tariff)
    )
    await callback.answer("Тариф обновлён!")


# Traffic menu actions
@router.callback_query(F.data == "traffic:general")
async def cb_traffic_general(callback: CallbackQuery):
    """Show general traffic from menu."""
    # Show processing
    await callback.message.edit_text("🚦 Получаю данные о пробках...")

    # Get traffic data
    moscow_traffic = await traffic_service.get_moscow_traffic()
    mkad_traffic = await traffic_service.get_mkad_traffic()
    ttk_traffic = await traffic_service.get_ttk_traffic()

    if not moscow_traffic:
        await callback.message.edit_text(
            "❌ Не удалось получить данные о пробках.\n"
            "Попробуйте позже.",
            reply_markup=traffic_menu_keyboard()
        )
        await callback.answer()
        return

    # Format response
    text = (
        f"🚦 <b>Дорожная обстановка</b>\n\n"
        f"{moscow_traffic.emoji} <b>Москва:</b> {moscow_traffic.status_text} ({moscow_traffic.level}/10)\n"
    )

    if mkad_traffic:
        text += f"{mkad_traffic.emoji} <b>МКАД:</b> {mkad_traffic.status_text} ({mkad_traffic.level}/10)\n"

    if ttk_traffic:
        text += f"{ttk_traffic.emoji} <b>ТТК:</b> {ttk_traffic.status_text} ({ttk_traffic.level}/10)\n"

    # Add forecast
    forecast = await traffic_service.get_traffic_forecast("moscow")
    if forecast:
        text += f"\n📊 <b>Прогноз на час:</b> {forecast.trend_emoji} {forecast.trend_text} ({forecast.forecast_level}/10)\n"

    # Add recommendation
    coeffs = get_cached_coefficients()
    if coeffs:
        max_coeff = max(c.coefficient for c in coeffs)
        recommendation = traffic_service.get_traffic_recommendation(moscow_traffic.level, max_coeff)
        text += f"\n💡 {recommendation}"

    text += f"\n\n🕐 Обновлено: {moscow_traffic.timestamp.strftime('%H:%M')}"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=traffic_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "traffic:mkad")
async def cb_traffic_mkad(callback: CallbackQuery):
    """Show MKAD traffic from menu."""
    await callback.message.edit_text("🚦 Получаю данные о МКАД...")

    mkad_traffic = await traffic_service.get_mkad_traffic()

    if not mkad_traffic:
        await callback.message.edit_text(
            "❌ Не удалось получить данные о пробках на МКАД.\n"
            "Попробуйте позже.",
            reply_markup=traffic_menu_keyboard()
        )
        await callback.answer()
        return

    text = (
        f"🚦 <b>МКАД</b>\n\n"
        f"{mkad_traffic.emoji} Загруженность: <b>{mkad_traffic.level}/10</b>\n"
        f"Статус: {mkad_traffic.status_text}\n"
    )

    # Add forecast
    forecast = await traffic_service.get_traffic_forecast("mkad")
    if forecast:
        text += f"📊 Прогноз на час: {forecast.trend_emoji} {forecast.trend_text} ({forecast.forecast_level}/10)\n"

    text += "\n"

    # Add tips
    if mkad_traffic.level <= 3:
        text += "✅ Отличное время для поездок по МКАД"
    elif mkad_traffic.level <= 6:
        text += "🟡 Средняя загруженность, возможны задержки"
    elif mkad_traffic.level <= 8:
        text += "🟠 Высокая загруженность, рекомендуем объездные пути"
    else:
        text += "🔴 Серьезные пробки, избегайте МКАД если возможно"

    text += f"\n\n🕐 Обновлено: {mkad_traffic.timestamp.strftime('%H:%M')}"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=traffic_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "traffic:ttk")
async def cb_traffic_ttk(callback: CallbackQuery):
    """Show TTK traffic from menu."""
    await callback.message.edit_text("🚦 Получаю данные о ТТК...")

    ttk_traffic = await traffic_service.get_ttk_traffic()

    if not ttk_traffic:
        await callback.message.edit_text(
            "❌ Не удалось получить данные о пробках на ТТК.\n"
            "Попробуйте позже.",
            reply_markup=traffic_menu_keyboard()
        )
        await callback.answer()
        return

    text = (
        f"🚦 <b>Третье транспортное кольцо (ТТК)</b>\n\n"
        f"{ttk_traffic.emoji} Загруженность: <b>{ttk_traffic.level}/10</b>\n"
        f"Статус: {ttk_traffic.status_text}\n"
    )

    # Add forecast
    forecast = await traffic_service.get_traffic_forecast("ttk")
    if forecast:
        text += f"📊 Прогноз на час: {forecast.trend_emoji} {forecast.trend_text} ({forecast.forecast_level}/10)\n"

    text += "\n"

    # Add tips
    if ttk_traffic.level <= 3:
        text += "✅ Отличное время для поездок по ТТК"
    elif ttk_traffic.level <= 6:
        text += "🟡 Средняя загруженность, возможны задержки"
    elif ttk_traffic.level <= 8:
        text += "🟠 Высокая загруженность, рекомендуем альтернативные маршруты"
    else:
        text += "🔴 Серьезные пробки, избегайте ТТК если возможно"

    text += f"\n\n🕐 Обновлено: {ttk_traffic.timestamp.strftime('%H:%M')}"

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=traffic_menu_keyboard()
    )
    await callback.answer()
