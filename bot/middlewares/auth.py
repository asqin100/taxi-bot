import time
import logging
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message

logger = logging.getLogger(__name__)


class ThrottleMiddleware(BaseMiddleware):
    """Simple per-user rate limiter."""

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self._last: dict[int, float] = defaultdict(float)

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
            now = time.monotonic()
            if now - self._last[uid] < self.rate_limit:
                logger.debug("Throttled user %s", uid)
                return
            self._last[uid] = now
        return await handler(event, data)
