from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.keyboards.inline import tariff_keyboard, zones_keyboard, event_types_keyboard

router = Router()


@router.message(Command("settings"))
async def cmd_settings(message: Message):
    await _send_tariff_selector(message)


@router.callback_query(F.data == "cmd:settings")
async def cb_settings(callback: CallbackQuery):
    from bot.keyboards.inline import settings_menu_keyboard
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Выберите раздел:",
        reply_markup=settings_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "settings:notifications")
async def cb_notifications_menu(callback: CallbackQuery):
    """Show notifications settings menu."""
    from bot.keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Основной тариф", callback_data="settings:preferred_tariff")],
        [InlineKeyboardButton(text="🚗 Выбрать тарифы", callback_data="settings:edit_tariffs")],
        [InlineKeyboardButton(text="📍 Выбрать зоны", callback_data="settings:edit_zones")],
        [InlineKeyboardButton(text="🎭 Типы мероприятий", callback_data="settings:edit_events")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="cmd:settings")],
    ])

    await callback.message.edit_text(
        "🔔 <b>НАСТРОЙКА УВЕДОМЛЕНИЙ</b>\n\n"
        "Выберите, что хотите настроить:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "settings:preferred_tariff")
async def cb_preferred_tariff_menu(callback: CallbackQuery):
    """Show preferred tariff selection menu."""
    user_id = callback.from_user.id

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            return

        current_tariff = user.preferred_tariff if hasattr(user, 'preferred_tariff') else "econom"

    from bot.keyboards.inline import InlineKeyboardMarkup, InlineKeyboardButton

    tariff_names = {
        "econom": "Эконом",
        "comfort": "Комфорт",
        "business": "Бизнес"
    }

    buttons = []
    for tariff_id, tariff_name in tariff_names.items():
        check = "✅ " if tariff_id == current_tariff else ""
        buttons.append([InlineKeyboardButton(
            text=f"{check}{tariff_name}",
            callback_data=f"settings:set_tariff:{tariff_id}"
        )])

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="settings:notifications")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(
        "🚗 <b>ОСНОВНОЙ ТАРИФ</b>\n\n"
        f"Текущий тариф: <b>{tariff_names.get(current_tariff, 'Эконом')}</b>\n\n"
        "Этот тариф будет использоваться для:\n"
        "• Функции 'Куда ехать'\n"
        "• Геоалертов\n"
        "• Уведомлений о коэффициентах\n\n"
        "Выберите тариф:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("settings:set_tariff:"))
async def cb_set_preferred_tariff(callback: CallbackQuery):
    """Set user's preferred tariff."""
    tariff = callback.data.split(":")[-1]
    user_id = callback.from_user.id

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one()
        user.preferred_tariff = tariff
        await session.commit()

    tariff_names = {
        "econom": "Эконом",
        "comfort": "Комфорт",
        "business": "Бизнес"
    }

    await callback.answer(f"✅ Установлен тариф: {tariff_names.get(tariff, tariff)}")

    # Refresh the menu
    await cb_preferred_tariff_menu(callback)


@router.callback_query(F.data == "settings:edit_tariffs")
async def cb_edit_tariffs(callback: CallbackQuery):
    """Edit tariff selection from notifications menu."""
    await _send_tariff_selector(callback.message, edit=True, from_notifications=True)
    await callback.answer()


@router.callback_query(F.data == "settings:edit_zones")
async def cb_edit_zones(callback: CallbackQuery):
    """Edit zone selection from notifications menu."""
    await _send_zone_selector(callback.message, edit=True, from_notifications=True)
    await callback.answer()


@router.callback_query(F.data == "settings:edit_events")
async def cb_edit_events(callback: CallbackQuery):
    """Edit event types from notifications menu."""
    await _send_event_type_selector(callback.message, edit=True, from_notifications=True)
    await callback.answer()


async def _send_tariff_selector(message: Message, edit: bool = False, from_notifications: bool = False):
    user = await _get_user(message)
    selected = set(user.tariffs.split(",")) if user.tariffs else set()

    # Check subscription for Business access
    from bot.services.subscription import check_feature_access
    tg_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    has_business = await check_feature_access(tg_id, "business_tariff")

    kb = tariff_keyboard(selected, has_business, from_notifications)
    text = (
        "🔔 <b>ВЫБОР ТАРИФОВ</b>\n\n"
        "Выберите тарифы, по которым вы хотите получать уведомления о высоких коэффициентах:\n\n"
        "🚗 <b>Эконом</b> — базовый тариф\n"
        "🚕 <b>Комфорт</b> — средний класс\n"
        "💼 <b>Бизнес</b> — премиум класс (Pro+)\n\n"
        "💡 Можно выбрать несколько тарифов"
    )

    if edit:
        await message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("tariff:"))
async def cb_tariff(callback: CallbackQuery):
    action_parts = callback.data.split(":")
    action = action_parts[1]
    from_notifications = len(action_parts) > 2 and action_parts[2] == "notif"

    if action == "done":
        if from_notifications:
            # Return to notifications menu
            await cb_notifications_menu(callback)
        else:
            # Continue to zone selector (original flow)
            await _send_zone_selector(callback.message, edit=True)
            await callback.answer()
        return

    # Check if trying to select Business tariff
    if action == "business":
        from bot.services.subscription import check_feature_access
        from bot.keyboards.inline import subscription_keyboard
        has_access = await check_feature_access(callback.from_user.id, "business_tariff")

        if not has_access:
            # Show upgrade prompt
            await callback.message.edit_text(
                "🔒 <b>Тариф Бизнес доступен только в Pro, Premium и Elite</b>\n\n"
                "Бизнес — самый дорогой класс такси с максимальными коэффициентами.\n\n"
                "💰 <b>Почему это важно:</b>\n"
                "• Коэффициенты на Бизнес обычно выше на 20-30%\n"
                "• Меньше конкуренции среди водителей\n"
                "• Более выгодные заказы\n\n"
                "Улучшите подписку, чтобы получить доступ:",
                reply_markup=subscription_keyboard(),
                parse_mode="HTML"
            )
            await callback.answer("🔒 Требуется Pro, Premium или Elite", show_alert=True)
            return

    # Continue with normal selection
    user = await _get_user(callback.message, tg_id=callback.from_user.id)
    selected = set(user.tariffs.split(",")) if user.tariffs else set()
    selected.discard("")

    if action in selected:
        selected.discard(action)
    else:
        selected.add(action)

    if not selected:
        selected.add("econom")

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        db_user = result.scalar_one()
        db_user.tariffs = ",".join(selected)
        await session.commit()

    # Pass subscription status to keyboard
    from bot.services.subscription import check_feature_access
    has_business = await check_feature_access(callback.from_user.id, "business_tariff")

    await callback.message.edit_reply_markup(reply_markup=tariff_keyboard(selected, has_business))
    await callback.answer("Обновлено")


async def _send_zone_selector(message: Message, edit: bool = False, from_notifications: bool = False):
    user = await _get_user(message)
    selected = set(user.zones.split(",")) if user.zones else set()
    selected.discard("")
    kb = zones_keyboard(selected, from_notifications)
    text = "📍 Выберите зоны интереса (или «Все зоны»):"
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("zone:"))
async def cb_zone(callback: CallbackQuery):
    action_parts = callback.data.split(":")
    action = action_parts[1]
    from_notifications = len(action_parts) > 2 and action_parts[2] == "notif"

    if action == "done":
        if from_notifications:
            # Return to notifications menu
            await cb_notifications_menu(callback)
        else:
            # Continue to event type selector (original flow)
            await _send_event_type_selector(callback.message, edit=True)
            await callback.answer()
        return

    user = await _get_user(callback.message, tg_id=callback.from_user.id)
    selected = set(user.zones.split(",")) if user.zones else set()
    selected.discard("")

    if action == "all":
        selected.clear()
    elif action in selected:
        selected.discard(action)
    else:
        selected.add(action)

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        db_user = result.scalar_one()
        db_user.zones = ",".join(selected)
        await session.commit()

    await callback.message.edit_reply_markup(reply_markup=zones_keyboard(selected))
    await callback.answer("Обновлено")


async def _send_event_type_selector(message: Message, edit: bool = False, from_notifications: bool = False):
    user = await _get_user(message)
    selected = set(user.event_types.split(",")) if user.event_types else set()
    selected.discard("")
    kb = event_types_keyboard(selected, from_notifications)
    text = "🎭 Выберите типы мероприятий для уведомлений:"
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("event_type:"))
async def cb_event_type(callback: CallbackQuery):
    action_parts = callback.data.split(":")
    action = action_parts[1]
    from_notifications = len(action_parts) > 2 and action_parts[2] == "notif"

    if action == "done":
        if from_notifications:
            # Return to notifications menu
            await cb_notifications_menu(callback)
        else:
            # Show success and return to main menu (original flow)
            from bot.services.subscription import get_subscription
            subscription = await get_subscription(callback.from_user.id)

            from bot.keyboards.inline import main_menu_keyboard
            await callback.message.edit_text("✅ Настройки сохранены!", reply_markup=main_menu_keyboard(subscription.tier))
            await callback.answer()
        return

    user = await _get_user(callback.message, tg_id=callback.from_user.id)
    selected = set(user.event_types.split(",")) if user.event_types else set()
    selected.discard("")

    if action in selected:
        selected.discard(action)
    else:
        selected.add(action)

    # Ensure at least one type is selected
    if not selected:
        selected.add("concert")

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        db_user = result.scalar_one()
        db_user.event_types = ",".join(selected)
        await session.commit()

    await callback.message.edit_reply_markup(reply_markup=event_types_keyboard(selected))
    await callback.answer("Обновлено")


async def _get_user(message: Message, tg_id: int | None = None) -> User:
    tid = tg_id or message.chat.id
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == tid))
        return result.scalar_one()
