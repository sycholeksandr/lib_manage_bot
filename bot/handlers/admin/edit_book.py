from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_edit_book_fields_keyboard
from bot.keyboards.reply import get_admin_keyboard
from bot.states.admin import AdminManageBookStates
from services.book_service import get_book_by_id_service, update_book_service

from .common import (
    ensure_admin_callback_access,
    ensure_admin_message_access,
    format_book_info,
    send_book_card_from_callback,
)

router = Router()


def _normalize_optional_text(value: str | None) -> str | None:
    """Convert '-' to None and trim text."""
    raw_value = (value or "").strip()
    return None if raw_value == "-" else raw_value


def _is_too_short(value: str | None, min_length: int = 2) -> bool:
    """Check whether optional text value is shorter than allowed."""
    return value is not None and len(value) < min_length


async def _get_edit_book_id_or_reset(
    message: Message,
    state: FSMContext,
) -> int | None:
    """Extract edited book id from state or reset flow on failure."""
    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return None

    return book_id


async def _handle_update_result(
    message: Message,
    result,
    success_text: str,
    session: AsyncSession,
) -> None:
    """Send unified response for book update operations."""
    if result == "book_not_found":
        await message.answer(
            "Книгу не знайдено.",
            reply_markup=get_admin_keyboard(),
        )
        return

    if result == "nothing_to_update":
        await message.answer(
            "Немає даних для оновлення.",
            reply_markup=get_admin_keyboard(),
        )
        return

    await message.answer(
        f"{success_text}\n\n{await format_book_info(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


@router.callback_query(F.data.startswith("overall_edit_book:"))
async def process_edit_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Open field selection menu for chosen book."""
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("overall_edit_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book = await get_book_by_id_service(
        session=session,
        book_id=int(book_id_str),
    )

    if book is None:
        await callback.message.edit_text("Книгу не знайдено.")
        await callback.answer()
        return

    await state.clear()
    await state.update_data(edit_book_id=book.id)

    await callback.message.answer(
        "Що саме ви хочете змінити?",
        reply_markup=get_edit_book_fields_keyboard(book.id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("book_edit_menu:"))
async def process_edit_book_menu(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Route admin to proper FSM state for selected editable field."""
    if not await ensure_admin_callback_access(callback, session):
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Некоректна дія.", show_alert=True)
        return

    _, action, book_id_str = parts

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    state_mapping = {
        "title": (
            AdminManageBookStates.waiting_for_new_title,
            "Введіть нову назву книги.",
        ),
        "author": (
            AdminManageBookStates.waiting_for_new_author,
            'Введіть нового автора або "-" щоб очистити поле.',
        ),
        "publisher": (
            AdminManageBookStates.waiting_for_new_publisher,
            'Введіть нове видавництво або "-" щоб очистити поле.',
        ),
        "genre": (
            AdminManageBookStates.waiting_for_new_genre,
            'Введіть новий жанр або "-" щоб очистити поле.',
        ),
        "language": (
            AdminManageBookStates.waiting_for_new_language,
            'Введіть нову мову або "-" щоб очистити поле.',
        ),
        "description": (
            AdminManageBookStates.waiting_for_new_description,
            'Введіть новий опис або "-" щоб очистити поле.',
        ),
    }

    if action == "cancel":
        book = await get_book_by_id_service(session=session, book_id=book_id)

        await state.clear()

        if book is None:
            await callback.message.edit_text("Книгу не знайдено.")
            await callback.message.answer(
                "Дію скасовано.",
                reply_markup=get_admin_keyboard(),
            )
            await callback.answer()
            return

        await send_book_card_from_callback(callback, session, book)
        await callback.message.answer(
            "Редагування скасовано.",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    if action not in state_mapping:
        await callback.answer("Невідома дія.", show_alert=True)
        return

    target_state, prompt = state_mapping[action]

    await state.clear()
    await state.update_data(edit_book_id=book_id)
    await state.set_state(target_state)
    await callback.message.answer(prompt)
    await callback.answer()


@router.message(AdminManageBookStates.waiting_for_new_title)
async def process_new_book_title(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update book title."""
    if not await ensure_admin_message_access(message, session):
        return

    new_title = (message.text or "").strip()

    if not new_title:
        await message.answer("Назва не може бути порожньою. Спробуйте ще раз.")
        return

    if len(new_title) < 2:
        await message.answer("Назва надто коротка. Спробуйте ще раз.")
        return

    book_id = await _get_edit_book_id_or_reset(message, state)
    if book_id is None:
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        title=new_title,
    )

    await state.clear()
    await _handle_update_result(
        message=message,
        result=result,
        success_text="✅ Назву книги успішно оновлено.",
        session=session,
    )


@router.message(AdminManageBookStates.waiting_for_new_author)
async def process_new_book_author(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update book author."""
    if not await ensure_admin_message_access(message, session):
        return

    new_author = _normalize_optional_text(message.text)

    if _is_too_short(new_author):
        await message.answer(
            'Автор надто короткий. Спробуйте ще раз або введіть "-" '
            "щоб очистити поле."
        )
        return

    book_id = await _get_edit_book_id_or_reset(message, state)
    if book_id is None:
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        author=new_author,
    )

    await state.clear()
    await _handle_update_result(
        message=message,
        result=result,
        success_text="✅ Автора книги успішно оновлено.",
        session=session,
    )


@router.message(AdminManageBookStates.waiting_for_new_publisher)
async def process_new_book_publisher(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update book publisher."""
    if not await ensure_admin_message_access(message, session):
        return

    new_publisher = _normalize_optional_text(message.text)

    if _is_too_short(new_publisher):
        await message.answer(
            'Видавництво надто коротке. Спробуйте ще раз або введіть "-" '
            "щоб очистити поле."
        )
        return

    book_id = await _get_edit_book_id_or_reset(message, state)
    if book_id is None:
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        publisher=new_publisher,
    )

    await state.clear()
    await _handle_update_result(
        message=message,
        result=result,
        success_text="✅ Видавництво книги успішно оновлено.",
        session=session,
    )


@router.message(AdminManageBookStates.waiting_for_new_genre)
async def process_new_book_genre(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update book genre."""
    if not await ensure_admin_message_access(message, session):
        return

    new_genre = _normalize_optional_text(message.text)

    if _is_too_short(new_genre):
        await message.answer(
            'Жанр надто короткий. Спробуйте ще раз або введіть "-" '
            "щоб очистити поле."
        )
        return

    book_id = await _get_edit_book_id_or_reset(message, state)
    if book_id is None:
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        genre=new_genre,
    )

    await state.clear()
    await _handle_update_result(
        message=message,
        result=result,
        success_text="✅ Жанр книги успішно оновлено.",
        session=session,
    )


@router.message(AdminManageBookStates.waiting_for_new_language)
async def process_new_book_language(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update book language."""
    if not await ensure_admin_message_access(message, session):
        return

    new_language = _normalize_optional_text(message.text)

    if _is_too_short(new_language):
        await message.answer(
            'Мова надто коротка. Спробуйте ще раз або введіть "-" '
            "щоб очистити поле."
        )
        return

    book_id = await _get_edit_book_id_or_reset(message, state)
    if book_id is None:
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        language=new_language,
    )

    await state.clear()
    await _handle_update_result(
        message=message,
        result=result,
        success_text="✅ Мову книги успішно оновлено.",
        session=session,
    )


@router.message(AdminManageBookStates.waiting_for_new_description)
async def process_new_book_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    """Update book description."""
    if not await ensure_admin_message_access(message, session):
        return

    new_description = _normalize_optional_text(message.text)

    book_id = await _get_edit_book_id_or_reset(message, state)
    if book_id is None:
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        description=new_description,
    )

    await state.clear()
    await _handle_update_result(
        message=message,
        result=result,
        success_text="✅ Опис книги успішно оновлено.",
        session=session,
    )