"""Search handler - find coefficients by address."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.geocoder import geocode_address, find_nearest_zone
from bot.services.zones import get_zones
from bot.services.yandex_api import get_cached_coefficients
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("search"))
async def cmd_search(message: Message):
    """Search for coefficients by address or metro station."""
    # Extract address from command
    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) < 2:
        await send_and_cleanup(
            message,
            "🔍 <b>Поиск коэффициента по адресу</b>\n\n"
            "Использование:\n"
            "<code>/search Красная площадь</code>\n"
            "<code>/search м. Тверская</code>\n"
            "<code>/search Шереметьево</code>",
            parse_mode="HTML"
        )
        return

    address = command_parts[1].strip()

    # Show processing message
    processing_msg = await send_and_cleanup(message, "🔍 Ищу адрес...")

    # Geocode address
    coords = await geocode_address(address)

    if not coords:
        await message.bot.edit_message_text(
            f"❌ Не удалось найти адрес: <b>{address}</b>\n\n"
            "Попробуйте уточнить запрос или использовать другой формат.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode="HTML"
        )
        return

    lat, lon = coords

    # Find nearest zone
    zones = get_zones()
    zone_id = find_nearest_zone(lat, lon, zones)

    if not zone_id:
        await message.bot.edit_message_text(
            "❌ Не удалось определить зону для этого адреса.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode="HTML"
        )
        return

    # Get zone info
    zone = next((z for z in zones if z.id == zone_id), None)
    if not zone:
        await message.bot.edit_message_text(
            "❌ Ошибка при получении информации о зоне.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode="HTML"
        )
        return

    # Get coefficients for this zone
    coeffs = get_cached_coefficients()
    zone_coeffs = [c for c in coeffs if c.zone_id == zone_id]

    if not zone_coeffs:
        await message.bot.edit_message_text(
            f"📍 <b>{address}</b>\n"
            f"Зона: {zone.name}\n\n"
            "⚠️ Нет данных о коэффициентах для этой зоны.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            parse_mode="HTML"
        )
        return

    # Format coefficients
    coeff_lines = []
    for c in sorted(zone_coeffs, key=lambda x: x.coefficient, reverse=True):
        emoji = "🔥" if c.coefficient >= 2.0 else "📈" if c.coefficient >= 1.5 else "📊"
        tariff_name = {
            "econom": "Эконом",
            "comfort": "Комфорт",
            "business": "Бизнес"
        }.get(c.tariff, c.tariff)
        coeff_lines.append(f"{emoji} {tariff_name}: <b>x{c.coefficient:.2f}</b>")

    # Create keyboard with action buttons
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Установить алерт", callback_data=f"alert_zone:{zone_id}")],
        [InlineKeyboardButton(text="🗺 Показать на карте", callback_data=f"map_zone:{zone_id}")],
    ])

    await message.bot.edit_message_text(
        f"📍 <b>{address}</b>\n"
        f"Зона: {zone.name}\n\n"
        f"<b>Текущие коэффициенты:</b>\n" + "\n".join(coeff_lines),
        chat_id=message.chat.id,
        message_id=processing_msg.message_id,
        parse_mode="HTML",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("alert_zone:"))
async def cb_alert_zone(callback):
    """Set alert for specific zone."""
    zone_id = callback.data.split(":")[1]

    # TODO: Implement alert setup for specific zone
    await callback.answer("Функция в разработке", show_alert=True)


@router.callback_query(F.data.startswith("map_zone:"))
async def cb_map_zone(callback):
    """Show zone on map."""
    # TODO: Implement map view for specific zone
    await callback.answer("Функция в разработке", show_alert=True)
