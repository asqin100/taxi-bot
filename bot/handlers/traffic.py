"""Traffic handlers - road conditions and recommendations."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.services import traffic as traffic_service
from bot.services.yandex_api import get_cached_coefficients
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("traffic"))
async def cmd_traffic(message: Message):
    """Show current traffic conditions in Moscow."""
    user_id = message.from_user.id

    # Check if user has access to traffic feature (Pro+)
    from bot.services.subscription import check_feature_access
    has_access = await check_feature_access(user_id, "traffic")

    if not has_access:
        await message.answer(
            "🔒 <b>Прогноз пробок</b>\n\n"
            "Эта функция доступна только в подписке Pro и выше.\n\n"
            "Улучшите подписку, чтобы получить доступ к:\n"
            "• Прогнозу пробок в реальном времени\n"
            "• Данным по МКАД и ТТК\n"
            "• Рекомендациям на основе коэффициентов",
            parse_mode="HTML"
        )
        return

    # Show processing message
    processing_msg = await send_and_cleanup(message, "🚦 Получаю данные о пробках...")

    # Clear cache to force fresh data
    traffic_service.clear_traffic_cache()

    # Get traffic data
    moscow_traffic = await traffic_service.get_moscow_traffic()
    mkad_traffic = await traffic_service.get_mkad_traffic()
    ttk_traffic = await traffic_service.get_ttk_traffic()

    if not moscow_traffic:
        await message.bot.edit_message_text(
            "❌ Не удалось получить данные о пробках.\n"
            "Попробуйте позже.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )
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

    # Add recommendation based on coefficients
    coeffs = get_cached_coefficients()
    if coeffs:
        max_coeff = max(c.coefficient for c in coeffs)
        recommendation = traffic_service.get_traffic_recommendation(moscow_traffic.level, max_coeff)
        text += f"\n💡 {recommendation}"

    text += f"\n\n🕐 Обновлено: {moscow_traffic.timestamp.strftime('%H:%M')}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
    ])

    await message.bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(Command("traffic_mkad"))
async def cmd_traffic_mkad(message: Message):
    """Show traffic conditions on MKAD."""
    user_id = message.from_user.id

    # Check if user has access to traffic feature (Pro+)
    from bot.services.subscription import check_feature_access
    has_access = await check_feature_access(user_id, "traffic")

    if not has_access:
        await message.answer(
            "🔒 Прогноз пробок доступен только в подписке Pro и выше",
            parse_mode="HTML"
        )
        return

    processing_msg = await send_and_cleanup(message, "🚦 Получаю данные о МКАД...")

    # Clear cache to force fresh data
    traffic_service.clear_traffic_cache()

    mkad_traffic = await traffic_service.get_mkad_traffic()

    if not mkad_traffic:
        await message.bot.edit_message_text(
            "❌ Не удалось получить данные о пробках на МКАД.\n"
            "Попробуйте позже.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )
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

    # Add tips based on traffic level
    if mkad_traffic.level <= 3:
        text += "✅ Отличное время для поездок по МКАД"
    elif mkad_traffic.level <= 6:
        text += "🟡 Средняя загруженность, возможны задержки"
    elif mkad_traffic.level <= 8:
        text += "🟠 Высокая загруженность, рекомендуем объездные пути"
    else:
        text += "🔴 Серьезные пробки, избегайте МКАД если возможно"

    text += f"\n\n🕐 Обновлено: {mkad_traffic.timestamp.strftime('%H:%M')}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
    ])

    await message.bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.message(Command("traffic_ttk"))
async def cmd_traffic_ttk(message: Message):
    """Show traffic conditions on TTK."""
    user_id = message.from_user.id

    # Check if user has access to traffic feature (Pro+)
    from bot.services.subscription import check_feature_access
    has_access = await check_feature_access(user_id, "traffic")

    if not has_access:
        await message.answer(
            "🔒 Прогноз пробок доступен только в подписке Pro и выше",
            parse_mode="HTML"
        )
        return

    processing_msg = await send_and_cleanup(message, "🚦 Получаю данные о ТТК...")

    # Clear cache to force fresh data
    traffic_service.clear_traffic_cache()

    ttk_traffic = await traffic_service.get_ttk_traffic()

    if not ttk_traffic:
        await message.bot.edit_message_text(
            "❌ Не удалось получить данные о пробках на ТТК.\n"
            "Попробуйте позже.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id
        )
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

    # Add tips based on traffic level
    if ttk_traffic.level <= 3:
        text += "✅ Отличное время для поездок по ТТК"
    elif ttk_traffic.level <= 6:
        text += "🟡 Средняя загруженность, возможны задержки"
    elif ttk_traffic.level <= 8:
        text += "🟠 Высокая загруженность, рекомендуем альтернативные маршруты"
    else:
        text += "🔴 Серьезные пробки, избегайте ТТК если возможно"

    text += f"\n\n🕐 Обновлено: {ttk_traffic.timestamp.strftime('%H:%M')}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="cmd:menu")]
    ])

    await message.bot.edit_message_text(
        text,
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )
