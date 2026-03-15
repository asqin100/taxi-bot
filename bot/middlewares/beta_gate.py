"""Middleware to restrict bot access during beta via invite promo codes.

Rule (when settings.restrict_beta_gate=True):
- Admins (settings.admin_ids) are always allowed.
- Everyone else must have at least one PromoCodeUsage record (entered promo once -> access forever).

Allowed without promo so user can unlock:
- /start message (so we can show prompt)
- Any message while FSM is PromoCodeStates.waiting_for_code (user enters promo)
"""

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from sqlalchemy import select, func as sa_func

from bot.config import settings
from bot.database.db import get_session
from bot.models.promo_code import PromoCodeUsage
from bot.handlers.promo_code import PromoCodeStates

logger = logging.getLogger(__name__)


def _admin_ids() -> set[int]:
    return {int(x.strip()) for x in (settings.admin_ids or "").split(",") if x.strip()}


async def _has_any_promo_usage(user_id: int) -> bool:
    async with get_session() as session:
        result = await session.execute(
            select(sa_func.count()).select_from(PromoCodeUsage).where(PromoCodeUsage.user_id == user_id)
        )
        return (result.scalar_one() or 0) > 0


class BetaGateMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not settings.restrict_beta_gate:
            return await handler(event, data)

        user_id = None
        message: Message | None = None

        if isinstance(event, Message):
            message = event
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            message = event.message
        else:
            return await handler(event, data)

        if not user_id:
            return await handler(event, data)

        if user_id in _admin_ids():
            return await handler(event, data)

        # Always allow /start so user can be prompted
        if isinstance(event, Message) and event.text and event.text.startswith("/start"):
            return await handler(event, data)

        # Allow entering promo code while we're waiting for it
        state = data.get("state")
        if state is not None:
            try:
                current = await state.get_state()
                if current == PromoCodeStates.waiting_for_code.state:
                    return await handler(event, data)
            except Exception:
                # If state can't be read for some reason, fall back to strict gating
                pass

        # Check permanent access
        if await _has_any_promo_usage(user_id):
            return await handler(event, data)

        # Block
        if isinstance(event, CallbackQuery):
            await event.answer("🔒 Нужен пригласительный промокод. Нажмите /start", show_alert=True)
            return

        if message is not None:
            await message.answer("🔒 Нужен пригласительный промокод. Нажмите /start")
        return
