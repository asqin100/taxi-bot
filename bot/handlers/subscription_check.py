"""Handler for channel subscription check."""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.config import settings

router = Router()


@router.callback_query(F.data == "check_subscription")
async def cb_check_subscription(callback: CallbackQuery) -> None:
    """Re-check if user subscribed to the channel."""
    user_id = callback.from_user.id

    try:
        member = await callback.bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)

        if member.status in ["member", "administrator", "creator"]:
            # User is subscribed
            await callback.answer("✅ Подписка подтверждена! Добро пожаловать!", show_alert=True)

            # Show main menu
            from bot.keyboards.inline import main_menu_keyboard

            text = (
                "🎉 <b>Добро пожаловать в KefPulse!</b>\n\n"
                "🚕 Твой умный помощник для максимального заработка в такси.\n\n"
                "Выбери действие:"
            )

            await callback.message.edit_text(
                text,
                reply_markup=main_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            # User is not subscribed yet
            await callback.answer(
                "❌ Вы ещё не подписались на канал. Пожалуйста, подпишитесь и попробуйте снова.",
                show_alert=True
            )
    except Exception as e:
        await callback.answer(
            "❌ Не удалось проверить подписку. Попробуйте позже.",
            show_alert=True
        )
