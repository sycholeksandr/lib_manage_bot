from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.book_service import get_taken_books_service

from .common import (
    build_users_with_taken_books_blocks,
    ensure_admin_message_access,
    send_chunked_messages,
)

router = Router()


@router.message(lambda message: message.text == "Користувачі")
async def list_users(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()

    taken_books = await get_taken_books_service(session=session)
    blocks = await build_users_with_taken_books_blocks(
        session=session,
        books=taken_books,
    )
    await send_chunked_messages(message, blocks)