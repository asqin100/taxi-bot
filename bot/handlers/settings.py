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
    await _send_tariff_selector(callback.message, edit=True)
    await callback.answer()


async def _send_tariff_selector(message: Message, edit: bool = False):
    user = await _get_user(message)
    selected = set(user.tariffs.split(",")) if user.tariffs else set()
    kb = tariff_keyboard(selected)
    text = "⚙️ Выберите тарифы для отслеживания:"
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("tariff:"))
async def cb_tariff(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    if action == "done":
        await _send_zone_selector(callback.message, edit=True)
        await callback.answer()
        return

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

    await callback.message.edit_reply_markup(reply_markup=tariff_keyboard(selected))
    await callback.answer("Обновлено")


async def _send_zone_selector(message: Message, edit: bool = False):
    user = await _get_user(message)
    selected = set(user.zones.split(",")) if user.zones else set()
    selected.discard("")
    kb = zones_keyboard(selected)
    text = "📍 Выберите зоны интереса (или «Все зоны»):"
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("zone:"))
async def cb_zone(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    if action == "done":
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


async def _send_event_type_selector(message: Message, edit: bool = False):
    user = await _get_user(message)
    selected = set(user.event_types.split(",")) if user.event_types else set()
    selected.discard("")
    kb = event_types_keyboard(selected)
    text = "🎭 Выберите типы мероприятий для уведомлений:"
    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.callback_query(F.data.startswith("event_type:"))
async def cb_event_type(callback: CallbackQuery):
    action = callback.data.split(":")[1]

    if action == "done":
        from bot.keyboards.inline import main_menu_keyboard
        await callback.message.edit_text("✅ Настройки сохранены!", reply_markup=main_menu_keyboard())
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
