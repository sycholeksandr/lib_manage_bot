from aiogram import Dispatcher

from bot.handlers.start import router as start_router
from bot.handlers.common import router as common_router
from bot.handlers.books import router as books_router
from bot.handlers.admin import router as admin_router

def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(common_router)
    dp.include_router(books_router)
    dp.include_router(admin_router)