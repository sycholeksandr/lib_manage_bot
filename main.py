import asyncio
import logging
import selectors

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.handlers.start import router as start_router
from bot.handlers.books import router as books_router
from bot.handlers.admin import get_admin_router
from bot.middlewares.db import DbSessionMiddleware
from core.config import settings
from db.connection import async_session_factory


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    admin_router = get_admin_router()
    
    dp.include_router(start_router)
    dp.include_router(books_router)
    dp.include_router(admin_router)

    dp.update.middleware(DbSessionMiddleware(async_session_factory))

    logging.info("Bot is starting...")
    await dp.start_polling(
        bot,
        allowed_updates=dp.resolve_used_update_types(),
    )


def selector_loop_factory() -> asyncio.SelectorEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


if __name__ == "__main__":
    try:
        asyncio.run(main(), loop_factory=selector_loop_factory)
    except KeyboardInterrupt:
        print("Bot stopped")