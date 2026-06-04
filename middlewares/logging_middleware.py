"""Logging middleware."""
import logging
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging incoming messages."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process event through middleware."""
        if isinstance(event, Message):
            user = event.from_user
            logger.info(
                f"Message from {user.id} (@{user.username}): "
                f"{event.text or '[media]'}"
            )
        
        return await handler(event, data)