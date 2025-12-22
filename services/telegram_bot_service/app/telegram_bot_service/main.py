"""Telegram bot entrypoint.

Runs as a script in Docker. Ensure the repository root is on sys.path so the
package imports are stable.
"""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import asyncio
import logging
from typing import Any

from aiogram import Bot, Dispatcher

from telegram_bot_service.settings import settings
from telegram_bot_service.handlers.user_handlers import router
from telegram_bot_service.services.rag_client import RAGClient, set_rag_client, get_rag_client


from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable


class AllowedUsersMiddleware(BaseMiddleware):
    def __init__(self, allowed_ids: set[int]) -> None:
        self._allowed = allowed_ids

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        if not self._allowed:
            return await handler(event, data)
        user = getattr(event, "from_user", None)
        if user and user.id in self._allowed:
            return await handler(event, data)
        # silently ignore or notify (here notify for messages/callbacks if possible)
        if hasattr(event, "answer"):
            try:
                await event.answer("Доступ ограничен.")
            except Exception:
                pass
        return None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup() -> None:
    client = RAGClient()
    await client.connect()
    set_rag_client(client)
    logger.info("Bot startup completed")


async def on_shutdown() -> None:
    try:
        await get_rag_client().close()
    except Exception:
        logger.exception("Failed to close RAG client")
    logger.info("Bot shutdown completed")


async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.message.middleware(AllowedUsersMiddleware(settings.allowed_ids()))
    dp.callback_query.middleware(AllowedUsersMiddleware(settings.allowed_ids()))
    dp.include_router(router)

    await on_startup()
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await on_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
