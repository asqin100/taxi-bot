"""Lunch feature - find nearby restaurants."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import aiohttp

from bot.config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:lunch")
async def cb_lunch_menu(callback: CallbackQuery):
    """Show lunch menu - search for nearby restaurants."""
    user_id = callback.from_user.id

    # Get user's last location
    from bot.database.db import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user or not user.last_latitude or not user.last_longitude:
            await callback.message.edit_text(
                "📍 <b>Геолокация не установлена</b>\n\n"
                "Для поиска ресторанов нужно сначала отправить свою геолокацию.\n\n"
                "Перейдите в Настройки → Уведомления → Обновить геолокацию",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📍 Настроить геолокацию", callback_data="geo_alerts:update_location")],
                    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
                ])
            )
            await callback.answer()
            return

    # Search for restaurants using Yandex Geocoder
    try:
        restaurants = await _search_restaurants(user.last_latitude, user.last_longitude)

        if not restaurants:
            await callback.message.edit_text(
                "🍽 <b>Рестораны не найдены</b>\n\n"
                "К сожалению, рядом с вашей локацией не найдено ресторанов.",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
                ])
            )
            await callback.answer()
            return

        # Format restaurant list
        text = "🍽 <b>Рестораны рядом с вами</b>\n\n"
        buttons = []

        for i, restaurant in enumerate(restaurants[:10], 1):
            name = restaurant.get("name", "Ресторан")
            address = restaurant.get("address", "")
            distance = restaurant.get("distance", 0)

            text += f"{i}. <b>{name}</b>\n"
            if address:
                text += f"   📍 {address}\n"
            text += f"   📏 ~{int(distance)}м\n\n"

            # Add button to open in maps
            lat = restaurant.get("lat")
            lon = restaurant.get("lon")
            if lat and lon:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🗺 {name}",
                        url=f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
                    )
                ])

        buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")])

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )
        await callback.answer()

    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        await callback.message.edit_text(
            "❌ <b>Ошибка поиска</b>\n\n"
            "Не удалось найти рестораны. Попробуйте позже.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")],
            ])
        )
        await callback.answer()


async def _search_restaurants(lat: float, lon: float, radius: int = 1000):
    """Search for restaurants near location using Yandex Geocoder."""
    if not settings.yandex_geocoder_key:
        logger.warning("YANDEX_GEOCODER_KEY not set")
        return []

    url = "https://geocode-maps.yandex.ru/1.x/"
    params = {
        "apikey": settings.yandex_geocoder_key,
        "geocode": f"{lon},{lat}",
        "kind": "house",
        "results": 10,
        "format": "json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status != 200:
                    logger.error(f"Yandex Geocoder error: {response.status}")
                    return []

                data = await response.json()

                # Parse response
                restaurants = []
                members = data.get("response", {}).get("GeoObjectCollection", {}).get("featureMember", [])

                for member in members:
                    geo_object = member.get("GeoObject", {})
                    name = geo_object.get("name", "")
                    description = geo_object.get("description", "")

                    # Check if it's a restaurant/cafe
                    if any(keyword in name.lower() or keyword in description.lower()
                           for keyword in ["ресторан", "кафе", "cafe", "restaurant", "столовая", "бар"]):

                        point = geo_object.get("Point", {}).get("pos", "").split()
                        if len(point) == 2:
                            rest_lon, rest_lat = float(point[0]), float(point[1])

                            # Calculate distance
                            from math import radians, sin, cos, sqrt, atan2
                            R = 6371000  # Earth radius in meters

                            lat1, lon1 = radians(lat), radians(lon)
                            lat2, lon2 = radians(rest_lat), radians(rest_lon)

                            dlat = lat2 - lat1
                            dlon = lon2 - lon1

                            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                            c = 2 * atan2(sqrt(a), sqrt(1-a))
                            distance = R * c

                            if distance <= radius:
                                restaurants.append({
                                    "name": name,
                                    "address": description,
                                    "lat": rest_lat,
                                    "lon": rest_lon,
                                    "distance": distance
                                })

                # Sort by distance
                restaurants.sort(key=lambda x: x["distance"])
                return restaurants

    except Exception as e:
        logger.error(f"Error in _search_restaurants: {e}")
        return []
