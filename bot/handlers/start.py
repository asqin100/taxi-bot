from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from bot.database.db import session_factory
from bot.models.user import User
from bot.keyboards.inline import main_menu_keyboard, tariff_keyboard
from bot.services.message_manager import send_and_cleanup

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    async with session_factory() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
            )
            session.add(user)
            await session.commit()

    await send_and_cleanup(
        message,
        "👋 Привет! Я бот-монитор коэффициентов Яндекс Такси.\n\n"
        "Помогу отслеживать зоны с высокими кэфами в Москве и МО.\n\n"
        "Команды:\n"
        "/kef — текущие коэффициенты\n"
        "/top — ТОП-5 зон\n"
        "/notify — уведомления\n"
        "/settings — настройки тарифов и зон\n"
        "/help — помощь",
        reply_markup=main_menu_keyboard(),
    )


@router.callback_query(F.data == "cmd:menu")
async def cb_menu(callback: CallbackQuery):
    await send_and_cleanup(
        callback.message,
        "📋 Главное меню",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.message(Command("help"))
async def cmd_help(message: Message):
    await send_and_cleanup(
        message,
        "ℹ️ Как пользоваться:\n\n"
        "1. Выберите тарифы в /settings\n"
        "2. Смотрите коэффициенты через /kef\n"
        "3. Включите уведомления через /notify — "
        "бот пришлёт сообщение, когда кэф вырастет выше вашего порога\n\n"
        "Данные обновляются каждые 2 минуты.",
        reply_markup=main_menu_keyboard(),
    )
