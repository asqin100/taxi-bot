"""CSV export handler for shifts."""
from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile, Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.services.export import export_shifts_csv, check_export_limit, log_export

router = Router()


@router.message(Command("export"))
async def cmd_export(message: Message) -> None:
    """Handle /export command"""
    await handle_export(message.from_user.id, message)


@router.callback_query(F.data == "menu_export")
async def cb_export(callback: CallbackQuery) -> None:
    """Handle export button from menu"""
    await handle_export(callback.from_user.id, callback)


async def handle_export(telegram_id: int, event) -> None:
    """
    Common handler for export functionality.

    Args:
        telegram_id: Telegram user ID
        event: Either Message or CallbackQuery
    """
    is_callback = isinstance(event, CallbackQuery)

    # Check rate limits
    can_export, limit_message = await check_export_limit(telegram_id)
    if not can_export:
        if is_callback:
            await event.answer(limit_message, show_alert=True)
        else:
            await event.answer(f"❌ {limit_message}")
        return

    # Generate CSV
    csv_data = await export_shifts_csv(telegram_id, days=30)
    csv_content = csv_data.getvalue()

    if not csv_content or csv_content.count('\n') <= 1:
        msg = "📭 Нет данных для экспорта за последние 30 дней."
        if is_callback:
            builder = InlineKeyboardBuilder()
            builder.button(text="🔙 Главное меню", callback_data="menu_main")
            await event.message.edit_text(msg, reply_markup=builder.as_markup())
            await event.answer()
        else:
            await event.answer(msg)
        return

    # Count shifts (subtract 1 for header)
    shifts_count = csv_content.count('\n') - 1

    # Log export
    await log_export(telegram_id, shifts_count)

    # Send file
    timestamp = int(datetime.now().timestamp()) if not is_callback else int(event.message.date.timestamp())
    filename = f"shifts_export_{telegram_id}_{timestamp}.csv"
    file = BufferedInputFile(csv_content.encode('utf-8-sig'), filename=filename)  # utf-8-sig for Excel compatibility

    caption = (
        f"📊 Экспорт завершен!\n"
        f"🚕 Смен: {shifts_count}\n"
        f"📅 Период: последние 30 дней\n\n"
        f"⚠️ Следующий экспорт будет доступен завтра"
    )

    if is_callback:
        await event.message.answer_document(file, caption=caption)
        await event.message.delete()
        await event.answer()
    else:
        await event.answer_document(file, caption=caption)
