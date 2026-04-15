from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_books_catalog_keyboard
from services.book_service import count_books_service, get_books_page_service

from .common import ensure_admin_callback_access, ensure_admin_message_access

router = Router()

BOOKS_PER_PAGE = 10


def format_book_catalog_page(books: list, current_page: int, total_books: int) -> str:
    if not books:
        return "Книг не знайдено."

    start_index = (current_page - 1) * BOOKS_PER_PAGE + 1
    end_index = start_index + len(books) - 1

    lines = [
        f"📚 <b>Книги</b> ({start_index}–{end_index} з {total_books})",
        "",
    ]

    for book in books:
        status = "на руках" if book.taken_by is not None else "доступна"
        lines.append(f"ID {book.id} — {book.title} — {status}")

    return "\n".join(lines)


async def build_books_catalog_payload(
    session: AsyncSession,
    page: int,
) -> tuple[str, int]:
    total_books = await count_books_service(session=session)

    if total_books == 0:
        return "Книг не знайдено.", 1

    total_pages = ceil(total_books / BOOKS_PER_PAGE)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * BOOKS_PER_PAGE

    books = await get_books_page_service(
        session=session,
        limit=BOOKS_PER_PAGE,
        offset=offset,
    )

    text = format_book_catalog_page(
        books=books,
        current_page=page,
        total_books=total_books,
    )
    return text, total_pages


@router.message(lambda message: message.text == "Книги")
async def show_books_catalog(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()

    page = 1
    text, total_pages = await build_books_catalog_payload(
        session=session,
        page=page,
    )

    await message.answer(
        text,
        reply_markup=get_books_catalog_keyboard(
            current_page=page,
            total_pages=total_pages,
        ),
    )


@router.callback_query(F.data.startswith("books_page:"))
async def paginate_books_catalog(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    page_str = callback.data.removeprefix("books_page:")

    if not page_str.isdigit():
        await callback.answer("Некоректна сторінка.", show_alert=True)
        return

    page = int(page_str)

    text, total_pages = await build_books_catalog_payload(
        session=session,
        page=page,
    )

    safe_page = max(1, min(page, total_pages))

    await callback.message.edit_text(
        text,
        reply_markup=get_books_catalog_keyboard(
            current_page=safe_page,
            total_pages=total_pages,
        ),
    )
    await callback.answer()