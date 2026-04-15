from aiogram import Router

from .add_book import router as add_book_router
from .common import router as common_router
from .delete_book import router as delete_book_router
from .edit_book import router as edit_book_router
from .force_return import router as force_return_router
from .manage_books import router as manage_books_router
from .qr import router as qr_router
from .users import router as users_router


def get_admin_router() -> Router:
    router = Router()
    router.include_router(common_router)
    router.include_router(add_book_router)
    router.include_router(manage_books_router)
    router.include_router(edit_book_router)
    router.include_router(delete_book_router)
    router.include_router(users_router)
    router.include_router(force_return_router)
    router.include_router(qr_router)
    return router