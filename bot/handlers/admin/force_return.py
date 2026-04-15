from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from services.book_service import force_return_book_service, get_book_by_id_service

from .common import ensure_admin_callback_access, send_book_card_from_callback

router = Router()


@router.callback_query(F.data.startswith("force_return_book:"))
async def process_force_return_book(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_callback_access(callback, session):
        return

    book_id_str = callback.data.removeprefix("force_return_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    result = await force_return_book_service(
        session=session,
        admin_id=callback.from_user.id,
        book_id=book_id,
    )

    if result == "book_not_found":
        await callback.answer("Книгу не знайдено.", show_alert=True)
        return

    if result == "success":
        book = await get_book_by_id_service(
            session=session,
            book_id=book_id,
        )

        await callback.answer("Книгу примусово повернуто.", show_alert=True)

        if book is not None:
            await callback.message.edit_text(
                "Оновлено інформацію про книгу після примусового повернення:\n\n"
                f"{await format_force_return_book(book, session)}",
                reply_markup=get_admin_book_actions_keyboard(
                    book.id,
                    is_taken=book.taken_by is not None,
                ),
            )
        return

    await callback.answer("Сталася невідома помилка.", show_alert=True)


async def format_force_return_book(book, session: AsyncSession) -> str:
    from .common import format_book_info
    return await format_book_info(book, session)


def get_admin_book_actions_keyboard(book_id: int, is_taken: bool = False):
    from bot.keyboards.inline import get_admin_book_actions_keyboard as keyboard
    return keyboard(book_id, is_taken=is_taken)