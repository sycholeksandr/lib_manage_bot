from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.book_service import get_book_by_id_service, take_book_service, return_book_service
from services.user_services import get_user_by_id_service
from bot.keyboards.inline import get_take_book_confirmation_keyboard, get_return_book_confirmation_keyboard

router = Router()

async def send_book_view(
    message: Message,
    session: AsyncSession,
    user_id: int,
    book_id: int,
) -> None:
    book = await get_book_by_id_service(
        session=session,
        book_id=book_id,
    )

    if book is None:
        await message.answer("Книгу не знайдено.")
        return

    if book.taken_by is None:
        await message.answer(
            f"📖 <b>{book.title}</b>\n\n"
            f"{book.description or 'Опис відсутній.'}\n\n"
            f"Статус: доступна\n"
        )

        await message.answer("Ви хочете взяти цю книгу?", reply_markup=get_take_book_confirmation_keyboard(book_id=book.id))
        
        return

    if book.taken_by == user_id:
        await message.answer(
            f"📖 <b>{book.title}</b>\n\n"
            f"{book.description or 'Опис відсутній.'}\n\n"
            f"Статус: ця книга зараз у вас\n"
        )
        await message.answer("Ви хочете повернути цю книгу?", reply_markup=get_return_book_confirmation_keyboard(book_id=book.id))
        return

    await message.answer(
        f"📖 <b>{book.title}</b>\n\n"
        f"{book.description or 'Опис відсутній.'}\n\n"
        f"Статус: зараз недоступна"
    )

@router.callback_query(F.data.startswith("take_book:"))
async def process_take_book(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    book_id_str = callback.data.removeprefix("take_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ідентифікатор книги.", show_alert=True)
        return

    book_id = int(book_id_str)
    user_id = callback.from_user.id

    result = await take_book_service(
        session=session,
        book_id=book_id,
        user_id=user_id,
    )

    if result == "success":
        await callback.message.edit_text("✅ Книгу успішно взято.")
        await callback.answer()
        return

    if result == "book_not_found":
        await callback.message.edit_text("❌ Книгу не знайдено.")
        await callback.answer()
        return

    if result == "book_already_taken":
        await callback.message.edit_text("⚠️ Ця книга вже зайнята.")
        await callback.answer()
        return
    if result == "user_book_limit_reached":
        await callback.message.edit_text("⚠️ Ви не можете взяти більше 3 книг одночасно.")
        await callback.answer()
        return
        
    await callback.message.edit_text("Сталася невідома помилка.")
    await callback.answer()

@router.callback_query(F.data.startswith("cancel_book_action:"))
async def process_cancel_book_action(
    callback: CallbackQuery,
) -> None:
    await callback.message.edit_text("Дію скасовано.")
    await callback.answer()
    
@router.callback_query(F.data.startswith("return_book:"))
async def process_return_book(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    book_id_str = callback.data.removeprefix("return_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ідентифікатор книги.", show_alert=True)
        return

    book_id = int(book_id_str)
    user_id = callback.from_user.id
    result = await return_book_service(
        session=session,
        book_id=book_id,
        user_id=user_id,
    )
    if result == "success":
        await callback.message.edit_text("✅ Книгу успішно повернуто.")
        await callback.answer()
        return  
    if result == "book_not_found":
        await callback.message.edit_text("❌ Книгу не знайдено.")
        await callback.answer()
        return
    if result == "book_not_taken":
        await callback.message.edit_text("⚠️ Ця книга не була взята.")
        await callback.answer()
        return
    
    await callback.message.edit_text("Сталася невідома помилка.")
    await callback.answer()
    
@router.callback_query(F.data.startswith("cancel_book_action:"))
async def process_cancel_book_action(
    callback: CallbackQuery,
) -> None:
    await callback.message.edit_text("Дію скасовано.")
    await callback.answer()