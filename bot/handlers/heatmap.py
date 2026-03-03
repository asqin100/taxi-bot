"""Heatmap handler for shift earnings visualization."""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.financial import get_shifts_by_period
from bot.services.visualization import generate_heatmap
from bot.services.subscription import check_feature_access

router = Router()


@router.message(Command("heatmap"))
async def cmd_heatmap(message: Message) -> None:
    """Handle /heatmap command to generate earnings heatmap."""
    # Check Elite subscription
    has_access = await check_feature_access(message.from_user.id, "heatmap")
    if not has_access:
        builder = InlineKeyboardBuilder()
        builder.button(text="⭐ Улучшить до Elite", callback_data="sub:upgrade")
        builder.adjust(1)

        await message.answer(
            "🔒 <b>Карта заработка доступна только в Elite подписке</b>\n\n"
            "С Elite подпиской вы получите:\n"
            "✅ Тепловую карту заработка по часам и дням\n"
            "✅ Визуализацию лучших времён для работы\n"
            "✅ Анализ 90 дней истории\n"
            "✅ Экспорт данных и калькулятор налогов\n\n"
            "💎 Elite — 999₽/месяц",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return

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
    # Check Elite subscription
    has_access = await check_feature_access(callback.from_user.id, "heatmap")
    if not has_access:
        builder = InlineKeyboardBuilder()
        builder.button(text="⭐ Улучшить до Elite", callback_data="sub:upgrade")
        builder.button(text="🔙 Назад", callback_data="cmd:menu")
        builder.adjust(1)

        await callback.message.edit_text(
            "🔒 <b>Карта заработка доступна только в Elite подписке</b>\n\n"
            "С Elite подпиской вы получите:\n"
            "✅ Тепловую карту заработка по часам и дням\n"
            "✅ Визуализацию лучших времён для работы\n"
            "✅ Анализ 90 дней истории\n"
            "✅ Экспорт данных и калькулятор налогов\n\n"
            "💎 Elite — 999₽/месяц",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Get all completed shifts for the user (last 90 days)
    shifts = await get_shifts_by_period(callback.from_user.id, days=90)

    if not shifts:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
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
        builder.button(text="🔙 Главное меню", callback_data="cmd:menu")

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
        builder.button(text="🔙 Главное меню", callback_data="cmd:menu")
        await callback.message.edit_text(
            f"❌ Ошибка при генерации тепловой карты: {str(e)}",
            reply_markup=builder.as_markup()
        )
        await callback.answer()
