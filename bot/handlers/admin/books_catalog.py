from math import ceil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    get_books_catalog_keyboard,
    get_book_separation_keyboard
)
from services.book_service import (
    count_books_service,
    get_books_page_service,
    count_available_books_service,
    count_taken_books_service
)
from bot.keyboards.reply import get_admin_keyboard

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
        status = "📕 на руках" if book.taken_by else "📗 доступна"
        lines.append(f"ID {book.id} — {book.title} — {status}")

    return "\n".join(lines)


async def build_books_catalog_payload(
    session: AsyncSession,
    page: int,
    filter_type: str,
) -> tuple[str, int]:
    if filter_type == "available":
        total_books = await count_available_books_service(session)
    elif filter_type == "taken":
        total_books = await count_taken_books_service(session)
    else:
        total_books = await count_books_service(session)

    if total_books == 0:
        return "Книг не знайдено.", 1

    total_pages = ceil(total_books / BOOKS_PER_PAGE)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * BOOKS_PER_PAGE

    if filter_type == "available":
        books = await get_books_page_service(
            session=session,
            limit=BOOKS_PER_PAGE,
            offset=offset,
            filter_type="available",
        )
    elif filter_type == "taken":
        books = await get_books_page_service(
            session=session,
            limit=BOOKS_PER_PAGE,
            offset=offset,
            filter_type="taken",
        )
    else:
        books = await get_books_page_service(
            session=session,
            limit=BOOKS_PER_PAGE,
            offset=offset,
            filter_type=None,
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
    await message.answer(
        "Оберіть, які книги показати:",
        reply_markup=get_book_separation_keyboard(),
    )


@router.callback_query(F.data.startswith("books_filter:"))
async def process_books_filter(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    filter_type = callback.data.removeprefix("books_filter:")

    if filter_type == "back":
        await callback.message.edit_text("Повернення до адмін-панелі.")
        await callback.message.answer(
            "Оберіть дію:",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    if filter_type not in {"available", "taken", "all"}:
        await callback.answer("Невідомий фільтр.", show_alert=True)
        return

    page = 1
    text, total_pages = await build_books_catalog_payload(
        session=session,
        page=page,
        filter_type=filter_type,
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_books_catalog_keyboard(
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
):
    if not await ensure_admin_callback_access(callback, session):
        return

    _, filter_type, page_str = callback.data.split(":")
    page = int(page_str)

    text, total_pages = await build_books_catalog_payload(
        session=session,
        page=page,
        filter_type=filter_type,
    )

    safe_page = max(1, min(page, total_pages))

    await callback.message.edit_text(
        text,
        reply_markup=get_books_catalog_keyboard(
            current_page=safe_page,
            total_pages=total_pages,
            filter_value=filter_type,
        ),
    )

    await callback.answer()
    
@router.callback_query(F.data == "noop")
async def process_noop_callback(callback: CallbackQuery) -> None:
    await callback.answer()