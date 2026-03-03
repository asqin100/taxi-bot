"""Heatmap handler for shift earnings visualization."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.financial import get_shifts_by_period
from bot.services.visualization import generate_heatmap

router = Router()


@router.message(Command("heatmap"))
async def cmd_heatmap(message: Message) -> None:
    """Handle /heatmap command to generate earnings heatmap."""
    # Get all completed shifts for the user (last 90 days)
    shifts = await get_shifts_by_period(message.from_user.id, days=90)

    if not shifts:
        await message.answer("📊 Нет завершенных смен для построения тепловой карты.")
        return

    # Generate heatmap
    await message.answer("⏳ Генерирую тепловую карту...")

    try:
        image_buffer = generate_heatmap(shifts)

        # Send image
        photo = BufferedInputFile(
            image_buffer.read(),
            filename="heatmap.png"
        )

        await message.answer_photo(
            photo=photo,
            caption=f"📊 Тепловая карта заработка\n"
                    f"Смен: {len(shifts)} (последние 90 дней)"
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при генерации тепловой карты: {str(e)}")


@router.callback_query(F.data == "menu_heatmap")
async def cb_heatmap(callback: CallbackQuery) -> None:
    """Handle heatmap callback from menu."""
    # Get all completed shifts for the user (last 90 days)
    shifts = await get_shifts_by_period(callback.from_user.id, days=90)

    if not shifts:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Главное меню", callback_data="menu_main")
        await callback.message.edit_text(
            "📊 Нет завершенных смен для построения тепловой карты.",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
        return

    # Generate heatmap
    await callback.answer("⏳ Генерирую тепловую карту...")

    try:
        image_buffer = generate_heatmap(shifts)

        # Send image
        photo = BufferedInputFile(
            image_buffer.read(),
            filename="heatmap.png"
        )

        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Главное меню", callback_data="menu_main")

        await callback.message.answer_photo(
            photo=photo,
            caption=f"📊 Тепловая карта заработка\n"
                    f"Смен: {len(shifts)} (последние 90 дней)",
            reply_markup=builder.as_markup()
        )

        # Delete the menu message
        await callback.message.delete()
    except Exception as e:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Главное меню", callback_data="menu_main")
        await callback.message.edit_text(
            f"❌ Ошибка при генерации тепловой карты: {str(e)}",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
