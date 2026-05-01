from aiogram import Dispatcher

from bot.handlers.start import router as start_router
from bot.handlers.admin.common import router as common_router
from bot.handlers.books import router as books_router
from bot.handlers.admin import get_admin_router
from bot.handlers.user import get_user_router

def register_routers(dp: Dispatcher) -> None:
    dp.include_router(start_router)
    dp.include_router(books_router)
    dp.include_router(get_admin_router())
    dp.include_router(get_user_router())