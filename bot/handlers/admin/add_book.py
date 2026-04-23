from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import get_admin_keyboard
from bot.states.admin import AdminAddBookStates
from services.book_service import create_book_service

from .common import ensure_admin_message_access, send_book_qr

router = Router()


def _normalize_optional_text(value: str | None) -> str | None:
    """Convert '-' to None and trim incoming text."""
    raw_value = (value or "").strip()
    return None if raw_value == "-" else raw_value


def _is_too_short(value: str | None, min_length: int = 2) -> bool:
    """Check whether optional text value is shorter than allowed."""
    return value is not None and len(value) < min_length


@router.message(lambda message: message.text == "Додати книгу")
async def start_add_book(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Start admin flow for creating a new book."""
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()
    await state.set_state(AdminAddBookStates.waiting_for_title)
    await message.answer("Введіть назву книги.")


@router.message(AdminAddBookStates.waiting_for_title)
async def process_book_title(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Save book title and move to author step."""
    if not await ensure_admin_message_access(message, session):
        return

    title = (message.text or "").strip()

    if not title:
        await message.answer(
            "Назва книги не може бути порожньою. Спробуйте ще раз."
        )
        return

    if len(title) < 2:
        await message.answer("Назва книги надто коротка. Спробуйте ще раз.")
        return

    await state.update_data(title=title)
    await state.set_state(AdminAddBookStates.waiting_for_author)
    await message.answer(
        'Введіть автора або "-" якщо поле треба залишити порожнім.'
    )


@router.message(AdminAddBookStates.waiting_for_author)
async def process_book_author(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Save author and move to publisher step."""
    if not await ensure_admin_message_access(message, session):
        return

    author = _normalize_optional_text(message.text)

    if _is_too_short(author):
        await message.answer(
            'Автор надто короткий. Спробуйте ще раз або введіть "-".'
        )
        return

    await state.update_data(author=author)
    await state.set_state(AdminAddBookStates.waiting_for_publisher)
    await message.answer(
        'Введіть видавництво або "-" якщо поле треба залишити порожнім.'
    )


@router.message(AdminAddBookStates.waiting_for_publisher)
async def process_book_publisher(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Save publisher and move to genre step."""
    if not await ensure_admin_message_access(message, session):
        return

    publisher = _normalize_optional_text(message.text)

    if _is_too_short(publisher):
        await message.answer(
            'Видавництво надто коротке. Спробуйте ще раз або введіть "-".'
        )
        return

    await state.update_data(publisher=publisher)
    await state.set_state(AdminAddBookStates.waiting_for_genre)
    await message.answer(
        'Введіть жанр або "-" якщо поле треба залишити порожнім.'
    )


@router.message(AdminAddBookStates.waiting_for_genre)
async def process_book_genre(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Save genre and move to language step."""
    if not await ensure_admin_message_access(message, session):
        return

    genre = _normalize_optional_text(message.text)

    if _is_too_short(genre):
        await message.answer(
            'Жанр надто короткий. Спробуйте ще раз або введіть "-".'
        )
        return

    await state.update_data(genre=genre)
    await state.set_state(AdminAddBookStates.waiting_for_language)
    await message.answer(
        'Введіть мову або "-" якщо поле треба залишити порожнім.'
    )


@router.message(AdminAddBookStates.waiting_for_language)
async def process_book_language(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Save language and move to description step."""
    if not await ensure_admin_message_access(message, session):
        return

    language = _normalize_optional_text(message.text)

    if _is_too_short(language):
        await message.answer(
            'Мова надто коротка. Спробуйте ще раз або введіть "-".'
        )
        return

    await state.update_data(language=language)
    await state.set_state(AdminAddBookStates.waiting_for_description)
    await message.answer(
        'Тепер введіть опис книги або "-" якщо поле треба залишити порожнім.'
    )


@router.message(AdminAddBookStates.waiting_for_description)
async def process_book_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Create book after collecting all metadata."""
    if not await ensure_admin_message_access(message, session):
        return

    description = _normalize_optional_text(message.text)
    data = await state.get_data()
    title = data.get("title")

    if not title:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть додавання книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    book = await create_book_service(
        session=session,
        title=title,
        author=data.get("author"),
        publisher=data.get("publisher"),
        genre=data.get("genre"),
        language=data.get("language"),
        description=description,
    )

    await state.clear()

    await message.answer(
        "✅ Книгу успішно додано.\n\n"
        f"ID: {book.id}\n"
        f"Назва: {book.title}\n"
        f"Автор: {book.author or '—'}\n"
        f"Видавництво: {book.publisher or '—'}\n"
        f"Жанр: {book.genre or '—'}\n"
        f"Мова: {book.language or '—'}\n"
        f"Опис: {book.description or '—'}",
        reply_markup=get_admin_keyboard(),
    )

    await send_book_qr(message, book)