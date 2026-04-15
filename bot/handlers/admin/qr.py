from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.book_service import get_book_by_id_service

from .common import ensure_admin_callback_access, send_book_qr

router = Router()


@router.callback_query(F.data.startswith("show_qr_code:"))
async def process_show_qr_code(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("show_qr_code:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book = await get_book_by_id_service(
        session=session,
        book_id=int(book_id_str),
    )

    if book is None:
        await callback.answer("Книгу не знайдено.", show_alert=True)
        return

    await send_book_qr(callback.message, book)
    await callback.answer()