from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.keyboards.inline import notify_keyboard, threshold_keyboard, event_types_keyboard, quiet_hours_keyboard
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(Command("notify"))
async def cmd_notify(message: Message):
    user = await _get_user(message.from_user.id)
    event_types = user.event_types.split(",") if user.event_types else []
    event_types_str = ", ".join(event_types) if event_types else "не выбраны"

    quiet_hours_str = "выключены"
    if user.quiet_hours_enabled:
        quiet_hours_str = f"с {user.quiet_hours_start:02d}:00 до {user.quiet_hours_end:02d}:00"

    location_str = "не установлена"
    if user.last_latitude and user.last_longitude:
        location_str = f"{user.last_latitude:.4f}, {user.last_longitude:.4f}"

    await send_and_cleanup(
        message,
        f"🔔 <b>Настройки уведомлений</b>\n\n"
        f"📊 Коэффициенты: {'включены' if user.notify_enabled else 'выключены'}\n"
        f"   Порог: x{user.surge_threshold}\n\n"
        f"🎭 Мероприятия: {'включены' if user.event_notify_enabled else 'выключены'}\n"
        f"   Типы: {event_types_str}\n\n"
        f"📍 Геоалерты: {'включены' if user.geo_alerts_enabled else 'выключены'}\n"
        f"   Локация: {location_str}\n\n"
        f"🌙 Тихие часы: {quiet_hours_str}",
        reply_markup=notify_keyboard(user.notify_enabled, user.event_notify_enabled, user.quiet_hours_enabled, user.geo_alerts_enabled),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "cmd:notify")
async def cb_notify(callback: CallbackQuery):
    user = await _get_user(callback.from_user.id)
    event_types = user.event_types.split(",") if user.event_types else []
    event_types_str = ", ".join(event_types) if event_types else "не выбраны"

    quiet_hours_str = "выключены"
    if user.quiet_hours_enabled:
        quiet_hours_str = f"с {user.quiet_hours_start:02d}:00 до {user.quiet_hours_end:02d}:00"

    location_str = "не установлена"
    if user.last_latitude and user.last_longitude:
        location_str = f"{user.last_latitude:.4f}, {user.last_longitude:.4f}"

    await callback.message.edit_text(
        f"🔔 <b>Настройки уведомлений</b>\n\n"
        f"📊 Коэффициенты: {'включены' if user.notify_enabled else 'выключены'}\n"
        f"   Порог: x{user.surge_threshold}\n\n"
        f"🎭 Мероприятия: {'включены' if user.event_notify_enabled else 'выключены'}\n"
        f"   Типы: {event_types_str}\n\n"
        f"📍 Геоалерты: {'включены' if user.geo_alerts_enabled else 'выключены'}\n"
        f"   Локация: {location_str}\n\n"
        f"🌙 Тихие часы: {quiet_hours_str}",
        reply_markup=notify_keyboard(user.notify_enabled, user.event_notify_enabled, user.quiet_hours_enabled, user.geo_alerts_enabled),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "notify:toggle")
async def cb_toggle(callback: CallbackQuery):
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one()
        user.notify_enabled = not user.notify_enabled
        await session.commit()
        enabled = user.notify_enabled
        event_enabled = user.event_notify_enabled
        quiet_enabled = user.quiet_hours_enabled

    await callback.message.edit_reply_markup(reply_markup=notify_keyboard(enabled, event_enabled, quiet_enabled))
    status = "включены ✅" if enabled else "выключены ❌"
    await callback.answer(f"Уведомления о коэффициентах {status}")


@router.callback_query(F.data == "notify:event_toggle")
async def cb_event_toggle(callback: CallbackQuery):
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one()
        user.event_notify_enabled = not user.event_notify_enabled
        await session.commit()
        enabled = user.notify_enabled
        event_enabled = user.event_notify_enabled
        quiet_enabled = user.quiet_hours_enabled

    await callback.message.edit_reply_markup(reply_markup=notify_keyboard(enabled, event_enabled, quiet_enabled))
    status = "включены ✅" if event_enabled else "выключены ❌"
    await callback.answer(f"Уведомления о мероприятиях {status}")


@router.callback_query(F.data == "notify:quiet_toggle")
async def cb_quiet_toggle(callback: CallbackQuery):
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one()
        user.quiet_hours_enabled = not user.quiet_hours_enabled
        await session.commit()
        enabled = user.notify_enabled
        event_enabled = user.event_notify_enabled
        quiet_enabled = user.quiet_hours_enabled

    await callback.message.edit_reply_markup(reply_markup=notify_keyboard(enabled, event_enabled, quiet_enabled))
    status = "включены ✅" if quiet_enabled else "выключены ❌"
    await callback.answer(f"Тихие часы {status}")


@router.callback_query(F.data == "notify:quiet_hours")
async def cb_quiet_hours_menu(callback: CallbackQuery):
    user = await _get_user(callback.from_user.id)
    await callback.message.edit_text(
        f"⏰ <b>Настройка тихих часов</b>\n\n"
        f"Текущие настройки:\n"
        f"С {user.quiet_hours_start:02d}:00 до {user.quiet_hours_end:02d}:00\n\n"
        f"Выберите время начала:",
        reply_markup=quiet_hours_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


# Store temporary state for quiet hours setup
_quiet_hours_state = {}


@router.callback_query(F.data.startswith("quiet_hour:"))
async def cb_set_quiet_hour(callback: CallbackQuery):
    hour = int(callback.data.split(":")[1])
    user_id = callback.from_user.id

    # Check if we're setting start or end time
    if user_id not in _quiet_hours_state:
        # Setting start time
        _quiet_hours_state[user_id] = {"start": hour}
        await callback.message.edit_text(
            f"⏰ <b>Настройка тихих часов</b>\n\n"
            f"Начало: {hour:02d}:00\n\n"
            f"Теперь выберите время окончания:",
            reply_markup=quiet_hours_keyboard(),
            parse_mode="HTML"
        )
        await callback.answer()
    else:
        # Setting end time
        start_hour = _quiet_hours_state[user_id]["start"]
        end_hour = hour

        # Save to database
        async with session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one()
            user.quiet_hours_start = start_hour
            user.quiet_hours_end = end_hour
            user.quiet_hours_enabled = True
            await session.commit()

        # Clear state
        del _quiet_hours_state[user_id]

        # Return to notify menu
        user = await _get_user(user_id)
        event_types = user.event_types.split(",") if user.event_types else []
        event_types_str = ", ".join(event_types) if event_types else "не выбраны"

        await callback.message.edit_text(
            f"🔔 <b>Настройки уведомлений</b>\n\n"
            f"📊 Коэффициенты: {'включены' if user.notify_enabled else 'выключены'}\n"
            f"   Порог: x{user.surge_threshold}\n\n"
            f"🎭 Мероприятия: {'включены' if user.event_notify_enabled else 'выключены'}\n"
            f"   Типы: {event_types_str}\n\n"
            f"🌙 Тихие часы: с {start_hour:02d}:00 до {end_hour:02d}:00",
            reply_markup=notify_keyboard(user.notify_enabled, user.event_notify_enabled, user.quiet_hours_enabled),
            parse_mode="HTML",
        )
        await callback.answer(f"✅ Тихие часы установлены: {start_hour:02d}:00 - {end_hour:02d}:00")


@router.callback_query(F.data == "notify:event_types")
async def cb_event_types_menu(callback: CallbackQuery):
    user = await _get_user(callback.from_user.id)
    selected = set(user.event_types.split(",")) if user.event_types else set()
    selected.discard("")
    await callback.message.edit_text(
        "🎭 Выберите типы мероприятий для уведомлений:",
        reply_markup=event_types_keyboard(selected),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("event_type:"))
async def cb_event_type(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    if action == "done":
        user = await _get_user(callback.from_user.id)
        event_types = user.event_types.split(",") if user.event_types else []
        event_types_str = ", ".join(event_types) if event_types else "не выбраны"

        await callback.message.edit_text(
            f"🔔 <b>Настройки уведомлений</b>\n\n"
            f"📊 Коэффициенты: {'включены' if user.notify_enabled else 'выключены'}\n"
            f"   Порог: x{user.surge_threshold}\n\n"
            f"🎭 Мероприятия: {'включены' if user.event_notify_enabled else 'выключены'}\n"
            f"   Типы: {event_types_str}",
            reply_markup=notify_keyboard(user.notify_enabled, user.event_notify_enabled),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    user = await _get_user(callback.from_user.id)
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


@router.callback_query(F.data == "notify:threshold")
async def cb_threshold_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите порог коэффициента для уведомлений:",
        reply_markup=threshold_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("threshold:"))
async def cb_set_threshold(callback: CallbackQuery):
    value = float(callback.data.split(":")[1])
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == callback.from_user.id))
        user = result.scalar_one()
        user.surge_threshold = value
        await session.commit()

    from bot.keyboards.inline import main_menu_keyboard
    await callback.message.edit_text(f"✅ Порог установлен: x{value}", reply_markup=main_menu_keyboard())
    await callback.answer()


async def _get_user(tg_id: int) -> User:
    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        return result.scalar_one()
