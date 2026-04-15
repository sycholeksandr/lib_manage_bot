from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import get_delete_book_confirmation_keyboard
from bot.keyboards.reply import get_admin_keyboard
from services.book_service import delete_book_service, get_book_by_id_service

from .common import (
    ensure_admin_callback_access,
    send_book_card_from_callback,
)

router = Router()


@router.callback_query(F.data.startswith("delete_book:"))
async def process_delete_book_request(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("delete_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    await callback.message.edit_reply_markup(
        reply_markup=get_delete_book_confirmation_keyboard(int(book_id_str)),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_book:"))
async def process_confirm_delete_book(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("confirm_delete_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    result = await delete_book_service(
        session=session,
        book_id=int(book_id_str),
    )

    if result == "success":
        await callback.message.edit_text("✅ Книгу успішно видалено.")
    elif result == "book_not_found":
        await callback.message.edit_text("❌ Книгу не знайдено.")
    elif result == "book_is_taken":
        await callback.message.edit_text("⚠️ Книгу не можна видалити, бо вона зараз на руках.")
    else:
        await callback.message.edit_text("Сталася невідома помилка.")

    await callback.message.answer(
        "Повертаю вас до адмін-панелі.",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_delete_book:"))
async def process_cancel_delete_book(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("cancel_delete_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book = await get_book_by_id_service(
        session=session,
        book_id=int(book_id_str),
    )

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
        "Видалення скасовано.",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()