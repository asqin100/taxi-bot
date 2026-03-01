"""Event management handlers."""
import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services import events as event_service
from bot.services.zones import get_zones

logger = logging.getLogger(__name__)
router = Router()


class AddEventStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_zone = State()
    waiting_for_type = State()
    waiting_for_end_time = State()


@router.message(Command("events"))
async def cmd_events(message: Message):
    """Show upcoming events."""
    upcoming = await event_service.get_upcoming_events(limit=10)

    if not upcoming:
        await message.answer("📅 Нет запланированных мероприятий")
        return

    text = "📅 <b>Ближайшие мероприятия:</b>\n\n"
    for event in upcoming:
        time_str = event.end_time.strftime("%d.%m %H:%M")
        emoji = {
            "concert": "🎵",
            "sport": "⚽",
            "conference": "🎤",
        }.get(event.event_type, "📍")

        text += f"{emoji} <b>{event.name}</b>\n"
        text += f"   Зона: {event.zone_id}\n"
        text += f"   Окончание: {time_str}\n\n"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("addevent"))
async def cmd_add_event(message: Message, state: FSMContext):
    """Start adding a new event."""
    await message.answer(
        "📝 <b>Добавление мероприятия</b>\n\n"
        "Введите название мероприятия:",
        parse_mode="HTML"
    )
    await state.set_state(AddEventStates.waiting_for_name)


@router.message(AddEventStates.waiting_for_name)
async def process_event_name(message: Message, state: FSMContext):
    """Process event name."""
    await state.update_data(name=message.text)

    zones = get_zones()
    zone_list = "\n".join([f"• {z.id} - {z.name}" for z in zones[:10]])

    await message.answer(
        f"📍 <b>Выберите зону:</b>\n\n{zone_list}\n\n"
        "Введите ID зоны:",
        parse_mode="HTML"
    )
    await state.set_state(AddEventStates.waiting_for_zone)


@router.message(AddEventStates.waiting_for_zone)
async def process_event_zone(message: Message, state: FSMContext):
    """Process event zone."""
    zone_id = message.text.strip().lower()
    zones = get_zones()
    zone_ids = [z.id for z in zones]

    if zone_id not in zone_ids:
        await message.answer(
            f"❌ Зона '{zone_id}' не найдена. Попробуйте еще раз:"
        )
        return

    await state.update_data(zone_id=zone_id)

    await message.answer(
        "🎭 <b>Тип мероприятия:</b>\n\n"
        "• concert - Концерт\n"
        "• sport - Спортивное событие\n"
        "• conference - Конференция\n"
        "• other - Другое\n\n"
        "Введите тип:",
        parse_mode="HTML"
    )
    await state.set_state(AddEventStates.waiting_for_type)


@router.message(AddEventStates.waiting_for_type)
async def process_event_type(message: Message, state: FSMContext):
    """Process event type."""
    event_type = message.text.strip().lower()
    valid_types = ["concert", "sport", "conference", "other"]

    if event_type not in valid_types:
        await message.answer(
            f"❌ Неверный тип. Выберите из: {', '.join(valid_types)}"
        )
        return

    await state.update_data(event_type=event_type)

    await message.answer(
        "⏰ <b>Время окончания:</b>\n\n"
        "Введите в формате: ДД.ММ ЧЧ:ММ\n"
        "Например: 01.03 23:00",
        parse_mode="HTML"
    )
    await state.set_state(AddEventStates.waiting_for_end_time)


@router.message(AddEventStates.waiting_for_end_time)
async def process_event_end_time(message: Message, state: FSMContext):
    """Process event end time and create event."""
    try:
        # Parse date/time
        end_time = datetime.strptime(message.text.strip(), "%d.%m %H:%M")
        # Set year to current year
        end_time = end_time.replace(year=datetime.now().year)

        # If date is in the past, assume next year
        if end_time < datetime.now():
            end_time = end_time.replace(year=datetime.now().year + 1)

        data = await state.get_data()

        # Create event
        event = await event_service.create_event(
            name=data["name"],
            zone_id=data["zone_id"],
            event_type=data["event_type"],
            end_time=end_time,
        )

        await message.answer(
            f"✅ <b>Мероприятие добавлено!</b>\n\n"
            f"📝 {event.name}\n"
            f"📍 Зона: {event.zone_id}\n"
            f"⏰ Окончание: {end_time.strftime('%d.%m.%Y %H:%M')}",
            parse_mode="HTML"
        )

        await state.clear()

    except ValueError:
        await message.answer(
            "❌ Неверный формат времени. Используйте: ДД.ММ ЧЧ:ММ\n"
            "Например: 01.03 23:00"
        )
