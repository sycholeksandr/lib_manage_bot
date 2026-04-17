from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import get_admin_keyboard
from bot.states.admin import AdminManageBookStates
from services.book_service import get_book_by_id_service, update_book_service

from .common import (
    ensure_admin_callback_access,
    ensure_admin_message_access,
    send_book_card_from_callback,
)

router = Router()


def get_edit_book_fields_keyboard(book_id: int):
    from bot.keyboards.inline import get_edit_book_fields_keyboard
    return get_edit_book_fields_keyboard(book_id)


@router.callback_query(F.data.startswith("overall_edit_book:"))
async def process_edit_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
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

    if action == "title":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_title)
        await callback.message.answer("Введіть нову назву книги.")
        await callback.answer()
        return

    if action == "author":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_author)
        await callback.message.answer('Введіть нового автора або "-" щоб очистити поле.')
        await callback.answer()
        return

    if action == "publisher":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_publisher)
        await callback.message.answer('Введіть нове видавництво або "-" щоб очистити поле.')
        await callback.answer()
        return

    if action == "genre":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_genre)
        await callback.message.answer('Введіть новий жанр або "-" щоб очистити поле.')
        await callback.answer()
        return

    if action == "language":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_language)
        await callback.message.answer('Введіть нову мову або "-" щоб очистити поле.')
        await callback.answer()
        return

    if action == "description":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_description)
        await callback.message.answer('Введіть новий опис або "-" щоб очистити поле.')
        await callback.answer()
        return

    if action == "cancel":
        book = await get_book_by_id_service(
            session=session,
            book_id=book_id,
        )

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

    await callback.answer("Невідома дія.", show_alert=True)


@router.message(AdminManageBookStates.waiting_for_new_title)
async def process_new_book_title(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    new_title = (message.text or "").strip()

    if not new_title:
        await message.answer("Назва не може бути порожньою. Спробуйте ще раз.")
        return

    if len(new_title) < 2:
        await message.answer("Назва надто коротка. Спробуйте ще раз.")
        return

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        title=new_title,
    )

    await state.clear()

    if result == "book_not_found":
        await message.answer("Книгу не знайдено.", reply_markup=get_admin_keyboard())
        return

    if result == "nothing_to_update":
        await message.answer("Немає даних для оновлення.", reply_markup=get_admin_keyboard())
        return

    await message.answer(
        "✅ Назву книги успішно оновлено.\n\n"
        f"{await format_updated_book(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


@router.message(AdminManageBookStates.waiting_for_new_author)
async def process_new_book_author(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    raw_value = (message.text or "").strip()
    new_author = None if raw_value == "-" else raw_value

    if new_author is not None and len(new_author) < 2:
        await message.answer('Автор надто короткий. Спробуйте ще раз або введіть "-" щоб очистити поле.')
        return

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        author=new_author,
    )

    await state.clear()

    if result == "book_not_found":
        await message.answer("Книгу не знайдено.", reply_markup=get_admin_keyboard())
        return

    if result == "nothing_to_update":
        await message.answer("Немає даних для оновлення.", reply_markup=get_admin_keyboard())
        return

    await message.answer(
        "✅ Автора книги успішно оновлено.\n\n"
        f"{await format_updated_book(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


@router.message(AdminManageBookStates.waiting_for_new_publisher)
async def process_new_book_publisher(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    raw_value = (message.text or "").strip()
    new_publisher = None if raw_value == "-" else raw_value

    if new_publisher is not None and len(new_publisher) < 2:
        await message.answer('Видавництво надто коротке. Спробуйте ще раз або введіть "-" щоб очистити поле.')
        return

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        publisher=new_publisher,
    )

    await state.clear()

    if result == "book_not_found":
        await message.answer("Книгу не знайдено.", reply_markup=get_admin_keyboard())
        return

    if result == "nothing_to_update":
        await message.answer("Немає даних для оновлення.", reply_markup=get_admin_keyboard())
        return

    await message.answer(
        "✅ Видавництво книги успішно оновлено.\n\n"
        f"{await format_updated_book(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


@router.message(AdminManageBookStates.waiting_for_new_genre)
async def process_new_book_genre(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    raw_value = (message.text or "").strip()
    new_genre = None if raw_value == "-" else raw_value

    if new_genre is not None and len(new_genre) < 2:
        await message.answer('Жанр надто короткий. Спробуйте ще раз або введіть "-" щоб очистити поле.')
        return

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        genre=new_genre,
    )

    await state.clear()

    if result == "book_not_found":
        await message.answer("Книгу не знайдено.", reply_markup=get_admin_keyboard())
        return

    if result == "nothing_to_update":
        await message.answer("Немає даних для оновлення.", reply_markup=get_admin_keyboard())
        return

    await message.answer(
        "✅ Жанр книги успішно оновлено.\n\n"
        f"{await format_updated_book(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


@router.message(AdminManageBookStates.waiting_for_new_language)
async def process_new_book_language(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    raw_value = (message.text or "").strip()
    new_language = None if raw_value == "-" else raw_value

    if new_language is not None and len(new_language) < 2:
        await message.answer('Мова надто коротка. Спробуйте ще раз або введіть "-" щоб очистити поле.')
        return

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        language=new_language,
    )

    await state.clear()

    if result == "book_not_found":
        await message.answer("Книгу не знайдено.", reply_markup=get_admin_keyboard())
        return

    if result == "nothing_to_update":
        await message.answer("Немає даних для оновлення.", reply_markup=get_admin_keyboard())
        return

    await message.answer(
        "✅ Мову книги успішно оновлено.\n\n"
        f"{await format_updated_book(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


@router.message(AdminManageBookStates.waiting_for_new_description)
async def process_new_book_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    raw_value = (message.text or "").strip()
    new_description = None if raw_value == "-" else raw_value

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть редагування книги ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    result = await update_book_service(
        session=session,
        book_id=book_id,
        description=new_description,
    )

    await state.clear()

    if result == "book_not_found":
        await message.answer("Книгу не знайдено.", reply_markup=get_admin_keyboard())
        return

    if result == "nothing_to_update":
        await message.answer("Немає даних для оновлення.", reply_markup=get_admin_keyboard())
        return

    await message.answer(
        "✅ Опис книги успішно оновлено.\n\n"
        f"{await format_updated_book(result, session)}",
        reply_markup=get_admin_keyboard(),
    )


async def format_updated_book(book, session: AsyncSession) -> str:
    from .common import format_book_info
    return await format_book_info(book, session)