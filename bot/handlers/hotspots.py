"""Hotspots handler - airports, train stations, and other high-demand locations."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.hotspots import (
    get_all_airports,
    get_all_train_stations,
    get_hotspot_info,
    format_hotspot_info,
)
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.callback_query(F.data == "menu:hotspots")
async def cb_hotspots_menu(callback: CallbackQuery):
    """Show hotspots main menu."""
    text = (
        "🗺 <b>ГОРЯЧИЕ ТОЧКИ</b>\n\n"
        "Выберите категорию для просмотра актуальной информации:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✈️ Аэропорты", callback_data="hotspots:airports")],
        [InlineKeyboardButton(text="🚂 Вокзалы", callback_data="hotspots:stations")],
        [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
    ])

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "hotspots:airports")
async def cb_airports_list(callback: CallbackQuery):
    """Show list of airports."""
    airports = get_all_airports()

    text = "✈️ <b>АЭРОПОРТЫ МОСКВЫ</b>\n\nВыберите аэропорт для подробной информации:"

    buttons = []
    for airport in airports:
        buttons.append([
            InlineKeyboardButton(
                text=f"✈️ {airport.name}",
                callback_data=f"hotspot:view:{airport.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:hotspots")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "hotspots:stations")
async def cb_stations_list(callback: CallbackQuery):
    """Show list of train stations."""
    stations = get_all_train_stations()

    text = "🚂 <b>ВОКЗАЛЫ МОСКВЫ</b>\n\nВыберите вокзал для подробной информации:"

    buttons = []
    for station in stations:
        buttons.append([
            InlineKeyboardButton(
                text=f"🚂 {station.name}",
                callback_data=f"hotspot:view:{station.id}"
            )
        ])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:hotspots")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("hotspot:view:"))
async def cb_hotspot_view(callback: CallbackQuery):
    """Show detailed information about a specific hotspot."""
    hotspot_id = callback.data.split(":")[-1]

    hotspot = await get_hotspot_info(hotspot_id)

    if not hotspot:
        await callback.answer("Информация не найдена", show_alert=True)
        return

    text = format_hotspot_info(hotspot)

    # Determine back button based on hotspot type
    back_data = "hotspots:airports" if hotspot.type == "airport" else "hotspots:stations"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data=f"hotspot:view:{hotspot_id}"),
            InlineKeyboardButton(text="🗺 На карте", callback_data="cmd:kef"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=back_data)],
    ])

    await send_and_cleanup(callback.message, text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()
