"""Handlers for coefficient notification sorting."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.services.yandex_api import get_cached_coefficients
from bot.services.zones import get_zone_names_map

router = Router()

TARIFF_LABELS = {"econom": "Эконом", "comfort": "Комфорт", "business": "Бизнес"}


@router.callback_query(F.data.startswith("coef_sort:"))
async def cb_coef_sort(callback: CallbackQuery):
    """Handle coefficient sorting button clicks."""
    sort_mode = callback.data.split(":")[1]  # "name" or "coef"

    user_id = callback.from_user.id

    # Get user settings
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("Ошибка: пользователь не найден")
            return

    # Get current coefficients
    zone_names = get_zone_names_map()
    all_data = get_cached_coefficients()

    if not all_data:
        await callback.answer("Данные о коэффициентах недоступны")
        return

    # Filter by user preferences
    user_tariffs = set(user.tariffs.split(",")) if user.tariffs else {"econom"}
    user_zones = set(user.zones.split(",")) if user.zones else set()

    # Check business tariff access
    from bot.services.subscription import check_feature_access
    has_business = await check_feature_access(user_id, "business_tariff")

    if not has_business and "business" in user_tariffs:
        user_tariffs = {t for t in user_tariffs if t != "business"}

    # Build alerts list
    alerts = []
    for sd in all_data:
        if sd.coefficient < user.surge_threshold:
            continue
        if sd.tariff not in user_tariffs:
            continue
        if user_zones and sd.zone_id not in user_zones:
            continue

        zone_name = zone_names.get(sd.zone_id, sd.zone_id)
        tariff_label = TARIFF_LABELS.get(sd.tariff, sd.tariff)

        alerts.append({
            "zone": zone_name,
            "tariff": tariff_label,
            "coef": sd.coefficient
        })

    if not alerts:
        await callback.answer("Нет зон с высокими коэффициентами")
        return

    # Sort alerts
    if sort_mode == "name":
        alerts.sort(key=lambda x: x["zone"])
        sort_text = "🔤 Сортировка: по имени"
    else:  # coef
        alerts.sort(key=lambda x: x["coef"], reverse=True)
        sort_text = "📊 Сортировка: по коэффициенту"

    # Format message
    alert_lines = [f"  {a['zone']} — {a['tariff']}: x{a['coef']}" for a in alerts]
    text = f"🔔 Высокие коэффициенты!\n{sort_text}\n\n" + "\n".join(alert_lines)

    # Update keyboard to show current sort mode
    if sort_mode == "name":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Сортировать по коэффициенту", callback_data="coef_sort:coef")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔤 Сортировать по имени", callback_data="coef_sort:name")],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
        ])

    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()
