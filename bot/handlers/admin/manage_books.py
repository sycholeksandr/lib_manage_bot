from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.admin import AdminManageBookStates
from services.book_service import get_book_by_id_service

from .common import ensure_admin_message_access, send_book_card

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