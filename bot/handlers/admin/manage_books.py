from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin import AdminManageBookStates
from services.book_service import get_book_by_id_service, duplicate_book_service
from bot.keyboards.reply import get_admin_keyboard

from .common import (
    ensure_admin_message_access,
    send_book_card,
    ensure_admin_callback_access,
    format_book_info
)

from bot.keyboards.inline import get_admin_book_actions_keyboard

router = Router()


@router.message(lambda message: message.text == "Керування книгами")
async def start_manage_books(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()
    await state.set_state(AdminManageBookStates.waiting_for_book_id)
    await message.answer("Введіть ID книги.")


@router.message(AdminManageBookStates.waiting_for_book_id)
async def process_book_id_for_manage(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    book_id_raw = (message.text or "").strip()

    if not book_id_raw.isdigit():
        await message.answer("ID книги має бути цілим числом. Спробуйте ще раз.")
        return

    book = await get_book_by_id_service(
        session=session,
        book_id=int(book_id_raw),
    )

    if book is None:
        await message.answer("Книгу з таким ID не знайдено.")
        return

    await state.clear()
    await send_book_card(message, session, book)

@router.callback_query(F.data.startswith("duplicate_book:"))
async def process_duplicate_book_request(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("duplicate_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    book = await get_book_by_id_service(
        session=session,
        book_id=book_id,
    )

    if book is None:
        await callback.answer("Книгу не знайдено.", show_alert=True)
        return

    await state.clear()
    await state.update_data(duplicate_book_id=book_id)
    await state.set_state(AdminManageBookStates.waiting_for_duplicate_count)

    await callback.message.answer(
        "Скільки копій створити?\n\n"
        "Введіть число від 1 до 50."
    )
    await callback.answer()

@router.message(AdminManageBookStates.waiting_for_duplicate_count)
async def process_duplicate_book_count(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    count_raw = (message.text or "").strip()

    if not count_raw.isdigit():
        await message.answer("Кількість має бути цілим числом. Спробуйте ще раз.")
        return

    count = int(count_raw)

    if count < 1:
        await message.answer("Кількість має бути більшою за 0.")
        return

    if count > 50:
        await message.answer("За один раз можна створити не більше 50 копій.")
        return

    data = await state.get_data()
    book_id = data.get("duplicate_book_id")

    if book_id is None:
        await state.clear()
        await message.answer(
            "Сталася помилка стану. Почніть створення копій ще раз.",
            reply_markup=get_admin_keyboard(),
        )
        return

    created_books = await duplicate_book_service(
        session=session,
        book_id=book_id,
        count=count,
    )

    await state.clear()

    if created_books is None:
        await message.answer(
            "Книгу не знайдено.",
            reply_markup=get_admin_keyboard(),
        )
        return

    created_ids = ", ".join(str(book.id) for book in created_books)

    await message.answer(
        f"✅ Створено копій: {len(created_books)}\n"
        f"Нові ID: {created_ids}",
        reply_markup=get_admin_keyboard(),
    )