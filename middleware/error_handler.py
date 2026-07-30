import logging
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery, Message
from typing import Callable, Dict, Any, Awaitable

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseMiddleware):
    """Catch handler errors and notify the user without crashing."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except Exception as exc:
            logger.error("Error in handler: %s", exc, exc_info=True)
            error_text = (
                "❌ *حدث خطأ*\n\n"
                "عذرًا، حدث خطأ مؤقت. يرجى المحاولة لاحقاً."
            )

            try:
                if isinstance(event, CallbackQuery):
                    await event.answer("عذرًا، حدث خطأ مؤقت. يرجى المحاولة لاحقاً.", show_alert=True)
                    if event.message:
                        await event.message.answer(error_text, parse_mode="Markdown")
                elif isinstance(event, Message):
                    await event.answer(error_text, parse_mode="Markdown")
            except Exception as msg_error:
                logger.error("Failed to send error message to user: %s", msg_error)

            return None
