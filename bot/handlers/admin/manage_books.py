from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin import AdminManageBookStates
from services.book_service import get_book_by_id_service, duplicate_book_service

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
async def process_duplicate_book(
    callback: CallbackQuery,
    session: AsyncSession,
):
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("duplicate_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    new_book = await duplicate_book_service(
        session=session,
        book_id=book_id,
    )

    if new_book is None:
        await callback.answer("Книгу не знайдено.", show_alert=True)
        return

    await callback.answer("Копію створено ✅", show_alert=True)

    await callback.message.answer(
        await format_book_info(new_book, session),
        reply_markup=get_admin_book_actions_keyboard(new_book.id),
    )