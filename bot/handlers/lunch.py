"""Lunch feature - find nearby restaurants."""
import asyncio
import logging
from math import radians, sin, cos, sqrt, atan2
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter


class LunchStates(StatesGroup):
    waiting_for_location = State()  # user pressed "lunch" and we wait for location


LUNCH_LOCATION_BUTTON_TEXT = "📍 Отправить геолокацию для обеда"
import aiohttp

from bot.config import settings

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "menu:lunch")
async def cb_lunch_menu(callback: CallbackQuery, state: FSMContext):
    """Lunch: always ask for current location before searching."""
    from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

    # Mark context so we don't steal location meant for other flows
    await state.set_state(LunchStates.waiting_for_location)

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=LUNCH_LOCATION_BUTTON_TEXT, request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await callback.message.answer(
        "🍽 <b>Заехать на обед</b>\n\n"
        "Чтобы показать актуальные точки рядом, пришлите <b>текущую</b> геолокацию.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(StateFilter(LunchStates.waiting_for_location), F.location)
async def lunch_location(message: Message, state: FSMContext):
    """Handle location for lunch search (only after pressing the lunch button)."""
    from aiogram.types import ReplyKeyboardRemove

    # Clear state first to avoid repeated captures
    await state.clear()

    user_id = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude

    # Remove the one-time reply keyboard immediately
    try:
        await message.answer("", reply_markup=ReplyKeyboardRemove())
    except Exception:
        pass


    # Search for restaurants
    try:
        logger.info(f"Searching restaurants for user {user_id} at ({lat}, {lon})")
        restaurants = await _search_restaurants(lat, lon)
        logger.info(f"Found {len(restaurants)} restaurants")

        if not restaurants:
            await message.answer(
                "🍽 <b>Рестораны не найдены</b>\n\n"
                "К сожалению, рядом с вашей локацией не найдено ресторанов в радиусе 10км.",
                parse_mode="HTML",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        # Format restaurant list
        text = "🍽 <b>Рестораны рядом с вами</b>\n\n"
        buttons = []

        for i, restaurant in enumerate(restaurants, 1):
            name = restaurant.get("name", "Ресторан")
            address = restaurant.get("address", "")
            distance = restaurant.get("distance", 0)

            if distance >= 1000:
                distance_str = f"~{distance/1000:.1f}км"
            else:
                distance_str = f"~{int(distance)}м"

            text += f"{i}. <b>{name}</b>\n"
            if address:
                text += f"   📍 {address}\n"
            text += f"   📏 {distance_str}\n\n"

            rest_lat = restaurant.get("lat")
            rest_lon = restaurant.get("lon")
            if rest_lat and rest_lon:
                # One compact button per place
                from bot.handlers.route_chooser import make_route_callback
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🧭 {name[:28]}",
                        callback_data=make_route_callback(rest_lat, rest_lon, "menu"),
                    )
                ])

        buttons.append([InlineKeyboardButton(text="◀️ Главное меню", callback_data="cmd:menu")])

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )
    finally:
        # Reply keyboard removed above
        pass

    # Stop here; old callback-based flow removed
    return

    # (old code below is unreachable)

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

        for i, restaurant in enumerate(restaurants, 1):
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

            # Add button to open in Yandex Maps
            lat = restaurant.get("lat")
            lon = restaurant.get("lon")
            if lat and lon:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🗺 {name[:25]}",
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


async def _search_restaurants(lat: float, lon: float, radius: int = 10000):
    """Search for restaurants near location using Nominatim (OpenStreetMap) API."""
    logger.info(f"Starting restaurant search at ({lat}, {lon}) with radius {radius}m")

    # Search for each restaurant chain separately
    restaurant_chains = ["Вкусно и точка", "KFC", "Бургер Кинг"]
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
        return all_restaurants[:3]

    except Exception as e:
        logger.error(f"Error in _search_restaurants: {e}", exc_info=True)
        return []

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

        for i, restaurant in enumerate(restaurants, 1):
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

            # Add button to open in Yandex Maps
            lat = restaurant.get("lat")
            lon = restaurant.get("lon")
            if lat and lon:
                buttons.append([
                    InlineKeyboardButton(
                        text=f"🗺 {name[:25]}",
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


async def _search_restaurants(lat: float, lon: float, radius: int = 10000):
    """Search for restaurants near location using Nominatim (OpenStreetMap) API."""
    logger.info(f"Starting restaurant search at ({lat}, {lon}) with radius {radius}m")

    # Search for each restaurant chain separately
    restaurant_chains = ["Вкусно и точка", "KFC", "Бургер Кинг"]
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
        return all_restaurants[:3]

    except Exception as e:
        logger.error(f"Error in _search_restaurants: {e}", exc_info=True)
        return []
