from datetime import timedelta

from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import get_main_menu_keyboard
from services.book_service import get_all_books_service, get_user_books_service
from services.user_services import get_user_by_id_service
from bot.handlers.admin.common import split_blocks_into_messages

router = Router()

def format_book_status(book) -> str:
    """Return user-facing availability status for a book."""
    return "📗 доступна" if book.taken_by is None else "📕 на руках"


def format_catalog_book_block(book) -> str:
    """Build one catalog item for regular users."""
    return (
        f"📚 <b>{book.title}</b>\n"
        f"<b>ID:</b> {book.id}\n"
        f"<b>Автор:</b> {book.author or '—'}\n"
        f"<b>Статус:</b> {format_book_status(book)}"
    )

def build_all_books_blocks(books: list) -> list[str] | str:
    """Build text catalog blocks for all library books."""
    if not books:
        return "У бібліотеці поки немає книг."

    return [format_catalog_book_block(book) for book in books]


def format_taken_at(book) -> str:
    """Format book taken date for user-facing messages."""
    return book.taken_at.strftime("%d.%m.%Y") if book.taken_at else "—"


def format_return_deadline(book) -> str:
    """Calculate and format current return deadline."""
    if not book.taken_at:
        return "—"

    deadline = book.taken_at + timedelta(days=21)
    return deadline.strftime("%d.%m.%Y")


def format_user_book_block(book) -> str:
    """Build one borrowed-book block for regular users."""
    return (
        f"📖 <b>{book.title}</b>\n"
        f"<b>ID:</b> {book.id}\n"
        f"<b>Автор:</b> {book.author or '—'}\n"
        f"<b>Взято:</b> {format_taken_at(book)}\n"
        f"<b>Повернути до:</b> {format_return_deadline(book)}"
    )

def build_user_books_blocks(books: list) -> list[str] | str:
    """Build blocks for books currently borrowed by user."""
    if not books:
        return "У вас зараз немає книг на руках."

    return [format_user_book_block(book) for book in books]

async def send_chunked_messages(
    message: Message,
    blocks: list[str] | str,
) -> None:
    """Send one or more messages depending on total text length."""
    if isinstance(blocks, str):
        await message.answer(
            blocks,
            reply_markup=get_main_menu_keyboard(),
        )
        return

    messages = split_blocks_into_messages(blocks)

    for index, text in enumerate(messages):
        if index == len(messages) - 1:
            await message.answer(
                text,
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            await message.answer(text)

@router.message(lambda message: message.text == "📚 Показати всі книги")
async def show_all_books(
    message: Message,
    session: AsyncSession,
) -> None:
    """Show all library books to regular users."""
    books = await get_all_books_service(session=session)
    blocks = build_all_books_blocks(books)

    await send_chunked_messages(message, blocks)


@router.message(lambda message: message.text == "📖 Книги у мене")
async def show_my_books(
    message: Message,
    session: AsyncSession,
) -> None:
    """Show books currently borrowed by the current user."""
    user = await get_user_by_id_service(
        session=session,
        user_id=message.from_user.id,
    )

    if user is None:
        await message.answer(
            "Спочатку потрібно пройти реєстрацію через /start.",
            reply_markup=get_main_menu_keyboard(),
        )
        return

    books = await get_user_books_service(
        session=session,
        user_id=user.id,
    )
    blocks = build_user_books_blocks(books)

    await send_chunked_messages(message, blocks)