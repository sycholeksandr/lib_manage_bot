from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.reply import get_admin_keyboard
from bot.states.admin import AdminAddBookStates
from services.book_service import create_book_service

from .common import (
    ensure_admin_message_access,
    send_book_qr,
)

router = Router()


@router.message(lambda message: message.text == "Додати книгу")
async def start_add_book(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()
    await state.set_state(AdminAddBookStates.waiting_for_title)
    await message.answer("Введіть назву книги та автора одним повідомленням.")


@router.message(AdminAddBookStates.waiting_for_title)
async def process_book_title(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    title = (message.text or "").strip()

    if not title:
        await message.answer("Назва книги не може бути порожньою. Спробуйте ще раз.")
        return

    if len(title) < 2:
        await message.answer("Назва книги надто коротка. Спробуйте ще раз.")
        return

    await state.update_data(title=title)
    await state.set_state(AdminAddBookStates.waiting_for_description)
    await message.answer("Тепер введіть опис книги.")


@router.message(AdminAddBookStates.waiting_for_description)
async def process_book_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    description = (message.text or "").strip()

    if not description:
        await message.answer("Опис книги не може бути порожнім. Спробуйте ще раз.")
        return

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
        description=description,
    )

    await state.clear()

    await message.answer(
        "✅ Книгу успішно додано.\n\n"
        f"ID: {book.id}\n"
        f"Назва: {book.title}\n"
        f"Опис: {book.description}",
        reply_markup=get_admin_keyboard(),
    )

    await send_book_qr(message, book)