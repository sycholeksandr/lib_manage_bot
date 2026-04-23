from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    get_admin_book_actions_keyboard,
    get_book_separation_keyboard,
    get_books_catalog_open_keyboard,
)
from bot.keyboards.reply import get_admin_keyboard
from services.book_service import (
    count_available_books_service,
    count_books_service,
    count_taken_books_service,
    get_book_by_id_service,
    get_books_page_service,
)

from .common import (
    ensure_admin_callback_access,
    ensure_admin_message_access,
    format_book_info,
)

router = Router()

BOOKS_PER_PAGE = 10
VALID_FILTERS = {"available", "taken", "all"}


def format_book_catalog_page(current_page: int, total_books: int) -> str:
    """Build short catalog header for current page."""
    start_index = (current_page - 1) * BOOKS_PER_PAGE + 1
    end_index = min(start_index + BOOKS_PER_PAGE - 1, total_books)

    return (
        f"📚 <b>Книги</b> ({start_index}–{end_index} з {total_books})\n"
        "Оберіть книгу:"
    )


async def _count_books_by_filter(
    session: AsyncSession,
    filter_type: str,
) -> int:
    """Return total amount of books for selected filter."""
    if filter_type == "available":
        return await count_available_books_service(session)
    if filter_type == "taken":
        return await count_taken_books_service(session)
    return await count_books_service(session)


async def build_books_catalog_payload(
    session: AsyncSession,
    page: int,
    filter_type: str,
) -> tuple[str, int, list]:
    """Build paginated catalog data for the selected filter."""
    total_books = await _count_books_by_filter(session, filter_type)

    if total_books == 0:
        return "Книг не знайдено.", 1, []

    total_pages = ceil(total_books / BOOKS_PER_PAGE)
    safe_page = max(1, min(page, total_pages))
    offset = (safe_page - 1) * BOOKS_PER_PAGE

    page_filter = filter_type if filter_type in {"available", "taken"} else None

    books = await get_books_page_service(
        session=session,
        limit=BOOKS_PER_PAGE,
        offset=offset,
        filter_type=page_filter,
    )

    text = format_book_catalog_page(
        current_page=safe_page,
        total_books=total_books,
    )
    return text, total_pages, books


@router.message(lambda message: message.text == "Книги")
async def show_books_catalog(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Show filter selection menu for admin books catalog."""
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()
    await message.answer(
        "Оберіть, які книги показати:",
        reply_markup=get_book_separation_keyboard(),
    )


@router.callback_query(F.data.startswith("books_filter:"))
async def process_books_filter(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Open first page of catalog for selected filter."""
    if not await ensure_admin_callback_access(callback, session):
        return

    filter_type = callback.data.removeprefix("books_filter:")

    if filter_type == "back":
        await callback.message.edit_text("Адмін-панель відкрита.")
        await callback.message.answer(
            "Оберіть дію:",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    if filter_type not in VALID_FILTERS:
        await callback.answer("Невідомий фільтр.", show_alert=True)
        return

    page = 1
    text, total_pages, books = await build_books_catalog_payload(
        session=session,
        page=page,
        filter_type=filter_type,
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_books_catalog_open_keyboard(
            books=books,
            current_page=page,
            total_pages=total_pages,
            filter_value=filter_type,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("books_page:"))
async def paginate_books(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Paginate catalog within the currently selected filter."""
    if not await ensure_admin_callback_access(callback, session):
        return

    _, filter_type, page_str = callback.data.split(":")
    page = int(page_str)

    text, total_pages, books = await build_books_catalog_payload(
        session=session,
        page=page,
        filter_type=filter_type,
    )

    safe_page = max(1, min(page, total_pages))

    await callback.message.edit_text(
        text,
        reply_markup=get_books_catalog_open_keyboard(
            books=books,
            current_page=safe_page,
            total_pages=total_pages,
            filter_value=filter_type,
        ),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("open_book_from_catalog:"))
async def open_book_from_catalog(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    """Open full book card from catalog entry."""
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("open_book_from_catalog:")

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

    await callback.message.edit_text(
        await format_book_info(book, session),
        reply_markup=get_admin_book_actions_keyboard(
            book.id,
            is_taken=book.taken_by is not None,
        ),
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def process_noop_callback(callback: CallbackQuery) -> None:
    """Silently ignore clicks on inactive pagination buttons."""
    await callback.answer()