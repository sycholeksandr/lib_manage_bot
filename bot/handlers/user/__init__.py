from aiogram import Router

from .books import router as books_router


def get_user_router() -> Router:
    """Collect all regular user routers."""
    router = Router()
    router.include_router(books_router)
    return router