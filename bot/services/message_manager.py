"""Message manager - keep chat clean by deleting old bot messages."""
import logging
from typing import Optional, Dict
from aiogram.types import Message, BufferedInputFile
from aiogram import Bot

logger = logging.getLogger(__name__)

# Store last message ID for each user
_last_messages: Dict[int, int] = {}


async def send_and_cleanup(
    message: Message,
    text: str,
    photo: Optional[BufferedInputFile] = None,
    **kwargs
) -> Message:
    """
    Send a message and delete the previous bot message.

    Args:
        message: User's message
        text: Text to send
        photo: Optional photo to send
        **kwargs: Additional arguments for message.answer()

    Returns:
        Sent message
    """
    user_id = message.from_user.id

    # Delete previous bot message if exists
    if user_id in _last_messages:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=_last_messages[user_id]
            )
        except Exception as e:
            logger.debug("Failed to delete previous message: %s", e)

    # Send new message (with or without photo)
    if photo:
        sent_message = await message.answer_photo(photo, caption=text, **kwargs)
    else:
        sent_message = await message.answer(text, **kwargs)

    # Store new message ID
    _last_messages[user_id] = sent_message.message_id

    return sent_message


async def edit_or_send(
    message: Message,
    text: str,
    **kwargs
) -> Message:
    """
    Try to edit the last message, or send a new one if editing fails.

    Args:
        message: User's message
        text: Text to send/edit
        **kwargs: Additional arguments

    Returns:
        Sent or edited message
    """
    user_id = message.from_user.id

    # Try to edit last message
    if user_id in _last_messages:
        try:
            await message.bot.edit_message_text(
                text=text,
                chat_id=message.chat.id,
                message_id=_last_messages[user_id],
                **kwargs
            )
            # Return a mock message object (editing doesn't return a new message)
            return message
        except Exception as e:
            logger.debug("Failed to edit message, sending new: %s", e)

    # Send new message if editing failed
    return await send_and_cleanup(message, text, **kwargs)


def clear_user_history(user_id: int):
    """Clear stored message ID for a user."""
    if user_id in _last_messages:
        del _last_messages[user_id]
