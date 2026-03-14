"""Route chooser: one button -> choose Navigator or Maps."""

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from bot.services.yandex_api import generate_yandex_maps_link, generate_yandex_navigator_link


def _fmt_coord(x: float) -> str:
    # keep callback_data short
    return f"{x:.5f}".rstrip("0").rstrip(".")


def make_route_callback(latitude: float, longitude: float, back: str) -> str:
    """Build compact callback_data for route chooser.

    back: "menu" or "advisor"
    """
    return f"route:{_fmt_coord(latitude)}:{_fmt_coord(longitude)}:{back}"


def route_choice_keyboard(latitude: float, longitude: float, back: str = "menu") -> InlineKeyboardMarkup:
    """Keyboard with a single button that expands into app choice."""
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🧭 Открыть маршрут", callback_data=make_route_callback(latitude, longitude, back))]]
    )


def route_apps_keyboard(latitude: float, longitude: float, back: str = "menu") -> InlineKeyboardMarkup:
    nav_url = generate_yandex_navigator_link(latitude, longitude)
    maps_url = generate_yandex_maps_link(latitude, longitude)

    back_cb = "menu:advisor" if back == "advisor" else "cmd:menu"

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚗 Навигатор", url=nav_url),
            InlineKeyboardButton(text="🗺 Карты", url=maps_url),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data=back_cb)],
    ])


async def handle_route_callback(callback: CallbackQuery):
    """Handle route:* callback by expanding markup to app choice."""
    try:
        # route:{lat}:{lon}:{back}
        _, lat_s, lon_s, back = callback.data.split(":", 3)
        lat = float(lat_s)
        lon = float(lon_s)
    except Exception:
        await callback.answer("❌ Неверные координаты", show_alert=True)
        return

    await callback.message.edit_reply_markup(reply_markup=route_apps_keyboard(lat, lon, back))
    await callback.answer()
