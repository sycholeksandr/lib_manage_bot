from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from services.book_service import get_book_by_id_service, get_all_books_service

from .common import ensure_admin_callback_access, send_book_qr, build_book_deep_link
from services.pdf_service import generate_qr_pdf
from services.qr_service import generate_qr_code_with_book_id
router = Router()


@router.callback_query(F.data.startswith("show_qr_code:"))
async def process_show_qr_code(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        await callback.answer("У вас немає доступу до цієї дії.", show_alert=True)
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
    
@router.message(Command("get_qr_pdf"))
async def process_get_qr_pdf(
    message: Message,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(message, session):
        await message.answer("У вас немає доступу до цієї дії.", show_alert=True)
        return

    books = await get_all_books_service(session=session)

    if not books:
        await message.answer("У базі немає книг для генерації PDF.")
        return

    pdf_buffer = generate_qr_pdf(
        books=books,
        qr_generator_func=generate_qr_code_with_book_id,
        deep_link_builder=build_book_deep_link,
    )

    pdf_file = BufferedInputFile(
        file=pdf_buffer.getvalue(),
        filename="library_qr_codes.pdf",
    )

    await message.answer_document(
        document=pdf_file,
        caption=f"PDF із QR-кодами книг. Загальна кількість: {len(books)}",
    )