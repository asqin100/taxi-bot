"""Middleware to check if user is banned."""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

from bot.services.admin import is_user_banned

logger = logging.getLogger(__name__)


class BanCheckMiddleware(BaseMiddleware):
    """Middleware to block banned users from using the bot."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Check if user is banned before processing update."""

        # Get user ID from event
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        # If we have user ID, check if banned
        if user_id:
            if await is_user_banned(user_id):
                logger.info(f"Blocked banned user {user_id}")

                # Send ban message
                if isinstance(event, Message):
                    await event.answer("❌ Доступ к боту заблокирован.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Доступ к боту заблокирован.", show_alert=True)

                # Don't call handler
                return

        # User is not banned, continue
        return await handler(event, data)
