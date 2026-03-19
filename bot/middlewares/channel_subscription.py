"""Middleware to check channel subscription before allowing bot usage."""
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import settings


class ChannelSubscriptionMiddleware(BaseMiddleware):
    """Check if user is subscribed to the required channel."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Skip check if channel_id is not configured
        if not settings.channel_id:
            return await handler(event, data)

        # Get user_id from event
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
            message = event
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            message = event.message
        else:
            # For other event types, skip check
            return await handler(event, data)

        # Skip check for /start command with referral parameter (to allow new users to see the bot)
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            # Allow /start to pass through, but we'll check subscription after
            pass

        # Check subscription
        bot = data["bot"]
        try:
            member = await bot.get_chat_member(chat_id=settings.channel_id, user_id=user_id)
            # Check if user is a member (member, administrator, creator)
            if member.status in ["member", "administrator", "creator"]:
                # User is subscribed, allow access
                return await handler(event, data)
        except Exception as e:
            # If we can't check (e.g., bot is not admin in channel), log and allow access
            import logging
            logging.warning(f"Failed to check channel subscription: {e}")
            return await handler(event, data)

        # User is not subscribed, show subscription required message
        builder = InlineKeyboardBuilder()
        builder.button(text="📢 Подписаться на канал", url=f"https://t.me/{settings.channel_id.lstrip('@')}")
        builder.button(text="✅ Я подписался", callback_data="check_subscription")
        builder.adjust(1)

        text = (
            "🔒 <b>Для использования бота необходимо подписаться на наш канал</b>\n\n"
            "📢 В канале:\n"
            "• Новости и обновления бота\n"
            "• Полезные советы для водителей\n"
            "• Анализ рынка такси\n"
            "• Эксклюзивные промокоды\n\n"
            "Подпишитесь и нажмите «Я подписался» ⬇️"
        )

        if isinstance(event, CallbackQuery):
            await event.answer("Необходима подписка на канал", show_alert=True)
            if message:
                try:
                    await message.edit_text(text, reply_markup=builder.as_markup(), parse_mode="HTML")
                except:
                    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
            await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

        # Don't call the handler
        return None
