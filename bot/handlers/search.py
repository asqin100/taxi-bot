"""Search handler - find coefficients by address."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.geocoder import geocode_address, find_nearest_zone
from bot.services.zones import get_zones
from bot.services.yandex_api import get_cached_coefficients
from bot.services.message_manager import send_and_cleanup

router = Router()


class SearchAddress(StatesGroup):
    waiting_for_address = State()


@router.callback_query(F.data == "menu:search")
async def cb_search_menu(callback: CallbackQuery, state: FSMContext):
    """Enter search mode from menu."""
    text = (
        "🔍 <b>ПОИСК ПО АДРЕСУ</b>\n\n"
        "Введите адрес, метро или название места:\n\n"
        "Примеры:\n"
        "  • Красная площадь\n"
        "  • м. Тверская\n"
        "  • Шереметьево\n"
        "  • Ленинский проспект 15"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cmd:menu")]
    ])

    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(SearchAddress.waiting_for_address)
    await callback.answer()


@router.message(Command("search"))
async def cmd_search(message: Message, state: FSMContext):
    """Search for coefficients by address or metro station."""
    # Extract address from command
    command_parts = message.text.split(maxsplit=1)

    if len(command_parts) < 2:
        # Enter search mode
        text = (
            "🔍 <b>ПОИСК ПО АДРЕСУ</b>\n\n"
            "Введите адрес, метро или название места:\n\n"
            "Примеры:\n"
            "  • Красная площадь\n"
            "  • м. Тверская\n"
            "  • Шереметьево\n"
            "  • Ленинский проспект 15"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cmd:menu")]
        ])

        await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
        await state.set_state(SearchAddress.waiting_for_address)
        return

    address = command_parts[1].strip()
    await _perform_search(message, address, state)


@router.message(SearchAddress.waiting_for_address)
async def process_address_search(message: Message, state: FSMContext):
    """Process address input in search mode."""
    address = message.text.strip()
    await _perform_search(message, address, state)


async def _perform_search(message: Message, address: str, state: FSMContext):
    """Perform address search and show results."""
    # Delete user's message and show processing message
    try:
        await message.delete()
    except:
        pass

    processing_msg = await message.answer("🔍 Ищу адрес...")

    # Geocode address
    coords = await geocode_address(address)

    if not coords:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="menu:search")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
        ])

        await message.bot.edit_message_text(
            f"❌ Не удалось найти адрес: <b>{address}</b>\n\n"
            "Попробуйте уточнить запрос или использовать другой формат.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.clear()
        return

    lat, lon = coords

    # Find nearest zone
    zones = get_zones()
    zone_id = find_nearest_zone(lat, lon, zones)

    if not zone_id:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="menu:search")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
        ])

        await message.bot.edit_message_text(
            "❌ Не удалось определить зону для этого адреса.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Get zone info
    zone = next((z for z in zones if z.id == zone_id), None)
    if not zone:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Попробовать снова", callback_data="menu:search")],
            [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
        ])

        await message.bot.edit_message_text(
            "❌ Ошибка при получении информации о зоне.",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.clear()
        return

    # Get coefficients for this zone
    coeffs = get_cached_coefficients()
    zone_coeffs = [c for c in coeffs if c.zone_id == zone_id]

    if not zone_coeffs:
        # Find nearby zones with data
        nearby_zones = _find_nearby_zones_with_data(lat, lon, zones, coeffs, exclude_zone=zone_id)

        if nearby_zones:
            nearby_text = "\n\n<b>Ближайшие зоны с данными:</b>\n"
            for nz_id, nz_name, distance in nearby_zones[:3]:
                nearby_text += f"  • {nz_name} (~{distance:.1f} км)\n"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"📍 {nz_name}", callback_data=f"show_zone:{nz_id}")]
                for nz_id, nz_name, _ in nearby_zones[:3]
            ] + [
                [InlineKeyboardButton(text="🔄 Другой адрес", callback_data="menu:search")],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
            ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Другой адрес", callback_data="menu:search")],
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")]
            ])
            nearby_text = ""

        await message.bot.edit_message_text(
            f"📍 <b>{address}</b>\n"
            f"Зона: {zone.name}\n\n"
            f"⚠️ Нет данных о коэффициентах для этой зоны.{nearby_text}",
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        await state.clear()
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
        [InlineKeyboardButton(text="🔄 Другой адрес", callback_data="menu:search")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
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
    await state.clear()


def _find_nearby_zones_with_data(lat: float, lon: float, zones: list, coeffs: list, exclude_zone: str = None, max_distance: float = 40.0):
    """Find nearby zones that have coefficient data."""
    import math

    def distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance using Haversine formula."""
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # Get zones with data
    zones_with_data = set(c.zone_id for c in coeffs)

    # Calculate distances
    nearby = []
    for zone in zones:
        if zone.id == exclude_zone or zone.id not in zones_with_data:
            continue

        dist = distance(lat, lon, zone.lat, zone.lon)
        if dist <= max_distance:
            nearby.append((zone.id, zone.name, dist))

    # Sort by distance
    nearby.sort(key=lambda x: x[2])
    return nearby


@router.callback_query(F.data.startswith("show_zone:"))
async def cb_show_zone(callback: CallbackQuery):
    """Show coefficients for a specific zone."""
    zone_id = callback.data.split(":")[1]

    zones = get_zones()
    zone = next((z for z in zones if z.id == zone_id), None)

    if not zone:
        await callback.answer("❌ Зона не найдена", show_alert=True)
        return

    coeffs = get_cached_coefficients()
    zone_coeffs = [c for c in coeffs if c.zone_id == zone_id]

    if not zone_coeffs:
        await callback.answer("❌ Нет данных для этой зоны", show_alert=True)
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Другой адрес", callback_data="menu:search")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await callback.message.edit_text(
        f"📍 <b>{zone.name}</b>\n\n"
        f"<b>Текущие коэффициенты:</b>\n" + "\n".join(coeff_lines),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("alert_zone:"))
async def cb_alert_zone(callback: CallbackQuery):
    """Set alert for specific zone."""
    zone_id = callback.data.split(":")[1]

    # TODO: Implement alert setup for specific zone
    await callback.answer("Функция в разработке", show_alert=True)


@router.callback_query(F.data.startswith("map_zone:"))
async def cb_map_zone(callback: CallbackQuery):
    """Show zone on map."""
    # TODO: Implement map view for specific zone
    await callback.answer("Функция в разработке", show_alert=True)
