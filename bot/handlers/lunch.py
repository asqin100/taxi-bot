"""Lunch feature - find nearby restaurants."""
import asyncio
import logging
from math import radians, sin, cos, sqrt, atan2
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

    # Search for restaurants
    try:
        logger.info(f"Searching restaurants for user {user_id} at ({user.last_latitude}, {user.last_longitude})")
        restaurants = await _search_restaurants(user.last_latitude, user.last_longitude)
        logger.info(f"Found {len(restaurants)} restaurants")

        if not restaurants:
            await callback.message.edit_text(
                "🍽 <b>Рестораны не найдены</b>\n\n"
                "К сожалению, рядом с вашей локацией не найдено ресторанов в радиусе 10км.\n\n"
                "Попробуйте обновить геолокацию или повторите попытку позже.",
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

            # Convert distance to km if > 1000m
            if distance >= 1000:
                distance_str = f"~{distance/1000:.1f}км"
            else:
                distance_str = f"~{int(distance)}м"

            text += f"{i}. <b>{name}</b>\n"
            if address:
                text += f"   📍 {address}\n"
            text += f"   📏 {distance_str}\n\n"

            # Add buttons to open in Yandex Maps and Navigator
            lat = restaurant.get("lat")
            lon = restaurant.get("lon")
            if lat and lon:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🗺 {name[:20]}... на карте",
                        url=f"https://yandex.ru/maps/?pt={lon},{lat}&z=16&l=map"
                    ),
                    InlineKeyboardButton(
                        text="🧭 Навигатор",
                        url=f"yandexnavi://build_route_on_map?lat_to={lat}&lon_to={lon}"
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


async def _search_restaurants(lat: float, lon: float, radius: int = 10000):
    """Search for restaurants near location using Nominatim (OpenStreetMap) API."""
    logger.info(f"Starting restaurant search at ({lat}, {lon}) with radius {radius}m")

    # Search for each restaurant chain separately
    restaurant_chains = ["Вкусно и точка", "Ростикс", "Бургер Кинг", "Burger King"]
    all_restaurants = []

    # Nominatim search endpoint
    url = "https://nominatim.openstreetmap.org/search"

    # Required User-Agent header for Nominatim
    headers = {
        "User-Agent": "KefPulse TaxiBot/1.0 (Telegram Bot for taxi drivers)"
    }

    try:
        async with aiohttp.ClientSession() as session:
            for chain in restaurant_chains:
                logger.info(f"Searching for chain: {chain}")

                # Calculate bounding box (~20km around user)
                lat_delta = 0.2  # ~20km
                lon_delta = 0.2

                params = {
                    "q": chain,
                    "format": "json",
                    "limit": 50,
                    "bounded": 1,
                    "viewbox": f"{lon-lon_delta},{lat-lat_delta},{lon+lon_delta},{lat+lat_delta}",
                }

                try:
                    async with session.get(url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                        logger.info(f"Nominatim response status for {chain}: {response.status}")

                        if response.status != 200:
                            response_text = await response.text()
                            logger.error(f"Nominatim API error for {chain}: {response.status}, response: {response_text[:200]}")
                            await asyncio.sleep(1)  # Rate limiting
                            continue

                        data = await response.json()
                        logger.info(f"Nominatim returned {len(data)} results for {chain}")

                        for item in data:
                            display_name = item.get("display_name", "")
                            rest_lat = float(item.get("lat", 0))
                            rest_lon = float(item.get("lon", 0))

                            # Calculate distance
                            R = 6371000  # Earth radius in meters

                            lat1, lon1 = radians(lat), radians(lon)
                            lat2, lon2 = radians(rest_lat), radians(rest_lon)

                            dlat = lat2 - lat1
                            dlon = lon2 - lon1

                            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                            c = 2 * atan2(sqrt(a), sqrt(1-a))
                            distance = R * c

                            if distance <= radius:
                                # Check if this restaurant is already in the list (avoid duplicates)
                                duplicate = False
                                for existing in all_restaurants:
                                    if abs(existing["lat"] - rest_lat) < 0.0001 and abs(existing["lon"] - rest_lon) < 0.0001:
                                        duplicate = True
                                        break

                                if not duplicate:
                                    # Extract name and address from display_name
                                    parts = display_name.split(", ")
                                    restaurant_name = parts[0] if parts else chain
                                    address = ", ".join(parts[1:4]) if len(parts) > 1 else ""

                                    all_restaurants.append({
                                        "name": restaurant_name,
                                        "address": address,
                                        "lat": rest_lat,
                                        "lon": rest_lon,
                                        "distance": distance
                                    })
                                    logger.debug(f"Added restaurant: {restaurant_name} at {distance/1000:.1f}km")

                        # Rate limiting for Nominatim (1 request per second)
                        await asyncio.sleep(1)

                except asyncio.TimeoutError:
                    logger.error(f"Timeout searching for {chain}")
                    await asyncio.sleep(1)
                    continue
                except Exception as e:
                    logger.error(f"Error searching for {chain}: {e}", exc_info=True)
                    await asyncio.sleep(1)
                    continue

        # Sort by distance
        all_restaurants.sort(key=lambda x: x["distance"])
        logger.info(f"Total restaurants found: {len(all_restaurants)}")
        return all_restaurants

    except Exception as e:
        logger.error(f"Error in _search_restaurants: {e}", exc_info=True)
        return []
