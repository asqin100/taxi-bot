from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton

from bot.services.yandex_api import get_cached_coefficients, get_top_zones
from bot.services.map_renderer import render_surge_map
from bot.services.traffic import get_moscow_traffic, get_traffic_recommendation
from bot.utils.helpers import format_surge_table, format_top_zones
from bot.keyboards.inline import main_menu_keyboard
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("kef"))
async def cmd_kef(message: Message):
    await _send_coefficients(message)


@router.callback_query(F.data == "cmd:kef")
async def cb_kef(callback: CallbackQuery):
    await _send_coefficients(callback.message, edit=False)
    await callback.answer()


async def _send_coefficients(message: Message, edit: bool = False):
    user_id = message.from_user.id

    # Get user subscription tier for menu
    from bot.services.subscription import get_subscription
    subscription = await get_subscription(user_id)

    data = get_cached_coefficients()
    text = format_surge_table(data)

    # Send map with text as caption
    img = render_surge_map(data)
    if img:
        photo = BufferedInputFile(img, filename="surge_map.png")
        await send_and_cleanup(
            message,
            text,
            photo=photo,
            reply_markup=main_menu_keyboard(subscription.tier)
        )
    else:
        await send_and_cleanup(message, text, reply_markup=main_menu_keyboard(subscription.tier))


@router.message(Command("top"))
async def cmd_top(message: Message):
    # Get user's selected tariffs from settings
    from bot.database.db import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
        user = result.scalar_one_or_none()

        # Use user's selected tariffs if available
        if user and user.tariffs:
            selected_tariffs = [t for t in user.tariffs.split(",") if t]
            # If single tariff selected, use it as filter
            tariff = selected_tariffs[0] if len(selected_tariffs) == 1 else None
        else:
            tariff = None

    await _send_top(message, tariff=tariff)


@router.callback_query(F.data == "cmd:top")
async def cb_top(callback: CallbackQuery):
    # Get user's selected tariffs from settings
    from bot.database.db import session_factory
    from bot.models.user import User
    from sqlalchemy import select

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one_or_none()

        # Use user's selected tariffs if available
        if user and user.tariffs:
            selected_tariffs = [t for t in user.tariffs.split(",") if t]
            # If multiple tariffs selected, show all of them (no filter)
            # If single tariff, use it as filter
            tariff = selected_tariffs[0] if len(selected_tariffs) == 1 else None
        else:
            tariff = None

    await _send_top(callback.message, tariff=tariff)
    await callback.answer()


@router.callback_query(F.data.startswith("top:tariff:"))
async def cb_top_tariff(callback: CallbackQuery):
    tariff = callback.data.split(":")[-1]

    # Check access for business tariff
    if tariff == "business":
        from bot.services.subscription import check_feature_access
        has_access = await check_feature_access(callback.from_user.id, "business_tariff")

        if not has_access:
            await callback.answer(
                "🔒 Тариф Бизнес доступен только в Pro, Premium и Elite подписках",
                show_alert=True
            )
            return

    await _send_top(callback.message, tariff=tariff if tariff != "all" else None)
    await callback.answer()


async def _send_top(message: Message, tariff: str | None = None):
    data = get_top_zones(5, tariff=tariff)
    text = format_top_zones(data)

    # Add current filter info
    if tariff:
        tariff_labels = {"econom": "Эконом", "comfort": "Комфорт", "business": "Бизнес"}
        text = f"🎯 <b>Фильтр:</b> {tariff_labels.get(tariff, tariff)}\n\n" + text

    # Add traffic info
    traffic = await get_moscow_traffic()
    if traffic:
        text += f"\n\n🚦 <b>Пробки сейчас:</b> {traffic.emoji} {traffic.status_text} ({traffic.level}/10)"

        # Smart recommendation based on top zone and traffic
        if data:
            top_coef = data[0].coefficient
            recommendation = get_traffic_recommendation(traffic.level, top_coef)
            text += f"\n{recommendation}"

    # Keyboard with filters
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚗 Эконом", callback_data="top:tariff:econom"),
            InlineKeyboardButton(text="🚙 Комфорт", callback_data="top:tariff:comfort"),
        ],
        [
            InlineKeyboardButton(text="🚕 Бизнес", callback_data="top:tariff:business"),
            InlineKeyboardButton(text="📊 Все", callback_data="top:tariff:all"),
        ],
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="cmd:top"),
        ],
        [InlineKeyboardButton(text="◀️ Мой кабинет", callback_data="menu:profile")],
    ])

    await send_and_cleanup(message, text, reply_markup=keyboard, parse_mode="HTML")
