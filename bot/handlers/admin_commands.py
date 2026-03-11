"""Admin commands for user management and bans."""
import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from bot.services.admin import ban_user, unban_user, get_banned_users, is_user_banned
from bot.config import settings

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    admin_ids = [int(id.strip()) for id in settings.admin_ids.split(",") if id.strip()]
    return user_id in admin_ids


@router.message(Command("ban"))
async def cmd_ban(message: Message):
    """Ban a user. Usage: /ban <user_id> [reason]"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 2:
        await message.answer("Использование: /ban <user_id> [причина]")
        return

    try:
        user_id = int(args[1])
        reason = args[2] if len(args) > 2 else "Нарушение правил"

        if await ban_user(user_id, reason):
            await message.answer(f"✅ Пользователь {user_id} забанен\nПричина: {reason}")
        else:
            await message.answer(f"❌ Не удалось забанить пользователя {user_id}")

    except ValueError:
        await message.answer("❌ Неверный ID пользователя")


@router.message(Command("unban"))
async def cmd_unban(message: Message):
    """Unban a user. Usage: /unban <user_id>"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /unban <user_id>")
        return

    try:
        user_id = int(args[1])

        if await unban_user(user_id):
            await message.answer(f"✅ Пользователь {user_id} разбанен")
        else:
            await message.answer(f"❌ Не удалось разбанить пользователя {user_id}")

    except ValueError:
        await message.answer("❌ Неверный ID пользователя")


@router.message(Command("banlist"))
async def cmd_banlist(message: Message):
    """Show list of banned users."""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    banned = await get_banned_users()

    if not banned:
        await message.answer("📋 Список банов пуст")
        return

    text = "🚫 <b>Забаненные пользователи:</b>\n\n"
    for user in banned[:20]:  # Show max 20
        text += f"• ID: <code>{user['telegram_id']}</code>\n"
        text += f"  Username: @{user['username']}\n"
        text += f"  Причина: {user['ban_reason']}\n"
        if user['banned_at']:
            text += f"  Дата: {user['banned_at'][:10]}\n"
        text += "\n"

    if len(banned) > 20:
        text += f"\n... и ещё {len(banned) - 20} пользователей"

    await message.answer(text, parse_mode="HTML")


@router.message(Command("checkban"))
async def cmd_checkban(message: Message):
    """Check if user is banned. Usage: /checkban <user_id>"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /checkban <user_id>")
        return

    try:
        user_id = int(args[1])
        is_banned = await is_user_banned(user_id)

        if is_banned:
            await message.answer(f"🚫 Пользователь {user_id} забанен")
        else:
            await message.answer(f"✅ Пользователь {user_id} не забанен")

    except ValueError:
        await message.answer("❌ Неверный ID пользователя")
