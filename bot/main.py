from __future__ import annotations
import asyncio, logging
from aiogram import Bot, Dispatcher
from bot.config import get_bot_settings
from bot.handlers.user_handlers import router

logging.basicConfig(level=logging.INFO)

async def main():
    settings = get_bot_settings()
    bot = Bot(token=settings.bot_token)
    bot["settings"] = settings

    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
