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
    delete_user_message: bool = True,
    **kwargs
) -> Message:
    """
    Send a message and delete the previous bot message.

    Args:
        message: User's message
        text: Text to send
        photo: Optional photo to send
        delete_user_message: Whether to delete user's message (default True)
        **kwargs: Additional arguments for message.answer()

    Returns:
        Sent message
    """
    user_id = message.from_user.id

    # Delete user's message to keep chat clean
    if delete_user_message:
        try:
            await message.delete()
        except Exception as e:
            logger.debug("Failed to delete user message: %s", e)

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


def split_long_message(text: str, max_length: int = 4000) -> list[str]:
    """
    Split long message into chunks that fit Telegram's limit.

    Args:
        text: Text to split
        max_length: Maximum length per chunk (default 4000 to leave room for formatting)

    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    for paragraph in paragraphs:
        # If adding this paragraph would exceed limit, save current chunk
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # If single paragraph is too long, split by sentences
            if len(paragraph) > max_length:
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 > max_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
                    else:
                        current_chunk += sentence + '. '
            else:
                current_chunk = paragraph + '\n\n'
        else:
            current_chunk += paragraph + '\n\n'

    # Add remaining chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
