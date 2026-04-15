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
    send_book_card_from_callback,
)

router = Router()


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

    if action == "description":
        await state.clear()
        await state.update_data(edit_book_id=book_id)
        await state.set_state(AdminManageBookStates.waiting_for_new_description)
        await callback.message.answer("Введіть новий опис книги.")
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


@router.message(AdminManageBookStates.waiting_for_new_description)
async def process_new_book_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    new_description = (message.text or "").strip()

    if not new_description:
        await message.answer("Опис не може бути порожнім. Спробуйте ще раз.")
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