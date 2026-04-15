from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings

from bot.keyboards.reply import get_admin_keyboard, get_remove_keyboard

from bot.keyboards.inline import (
    get_admin_book_actions_keyboard,
    get_delete_book_confirmation_keyboard,
    get_edit_book_fields_keyboard,
)

from bot.states.admin import AdminAddBookStates, AdminManageBookStates
from services.book_service import (
    create_book_service,
    get_book_by_id_service,
    update_book_service,
    delete_book_service,
    get_all_books_service,
    get_user_books_service,
    get_taken_books_service,
    force_return_book_service,
)
from services.user_services import get_user_by_id_service

from services.qr_service import generate_qr_code_with_book_id

router = Router()

async def if_admin_user(session: AsyncSession, user_id: int):
    user = await get_user_by_id_service(session=session, user_id=user_id)
    if user is None or not user.is_admin:
        return False
    return True

def build_book_deep_link(book_id: int) -> str:
    return f"https://t.me/{settings.TELEGRAM_BOT_NAME}?start=book_{book_id}"

async def format_book_info(book, session) -> str:
    taken_at_str = book.taken_at.strftime("%d.%m.%Y") if book.taken_at else "—"
    user = await get_user_by_id_service(
            session=session,
            user_id=book.taken_by
        )
    if book.taken_by is None:
        status = "доступна"
        taken_by_str = "—"
    else:
        status = "на руках"
        taken_by_str = user.full_name if user else str(book.taken_by)
    short_description = (
       book.description[:15] + "..."
       if book.description and len(book.description) > 15
       else (book.description or "Опис відсутній.")
    )
    telegram_line = (
        f'<b>Telegram:</b> <a href="https://t.me/{user.tg_username}">@{user.tg_username}</a>\n'
        if user and user.tg_username
        else ""
    )
    return (
        f"📖 <b>ID:</b> {book.id}\n"
        f"<b>Назва:</b> {book.title}\n"
        f"<b>Опис:</b> {short_description}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Взята:</b> {taken_by_str}\n"
        f"<b>Telegram:</b> {telegram_line}"
        f"<b>Дата взяття:</b> {taken_at_str}"
    )


def split_blocks_into_messages(blocks: list[str], max_length: int = 4000) -> list[str]:
    messages = []
    current_message = ""

    for block in blocks:
        if not current_message:
            current_message = block
            continue

        candidate = current_message + "\n----------------------\n" + block

        if len(candidate) <= max_length:
            current_message = candidate
        else:
            messages.append(current_message)
            current_message = block

    if current_message:
        messages.append(current_message)

    return messages


async def format_users_with_taken_books(session: AsyncSession, books: list) -> list[str] | str:
    if not books:
        return "Зараз немає користувачів, у яких книги на руках."

    grouped: dict[int, list] = {}

    for book in books:
        if book.taken_by is None:
            continue
        grouped.setdefault(book.taken_by, []).append(book)

    blocks = []

    for user_id, user_books in grouped.items():
        user = await get_user_by_id_service(
            session=session,
            user_id=user_id,
        )

        if user is None:
            continue

        lines = [
            f"👤 <b>{user.full_name}</b>",
            f"<b>Телефон:</b> {user.contact or '—'}",
        ]

        if user.tg_username:
            lines.append(
                f'<b>Telegram:</b> <a href="https://t.me/{user.tg_username}">@{user.tg_username}</a>'
            )

        lines.append("<b>Книги на руках:</b>")

        for book in user_books:
            taken_at_str = book.taken_at.strftime("%d.%m.%Y") if book.taken_at else "—"
            lines.append(f"• ID {book.id} — {book.title} ({taken_at_str})")

        blocks.append("\n".join(lines))

    if not blocks:
        return "Зараз немає коректних даних про користувачів з книгами на руках."

    return blocks

@router.message(Command("cancel"))
async def cancel_current_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    current_state = await state.get_state()

    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return
    
    if current_state is None:
        await message.answer("Наразі немає активної дії для скасування.")
        return
    await state.clear()
    await message.answer("Поточну дію скасовано.",
        reply_markup=get_admin_keyboard(),
        )

@router.message(Command("all_books"))
async def cmd_all_books(
    message: Message,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return

    books = await get_all_books_service(session=session)
    if not books:
        await message.answer("Книг не знайдено.")
        return

    book_info_list = [
        await format_book_info(book, session) for book in books
        
    ]
    messages = split_blocks_into_messages(book_info_list)
    for i, text in enumerate(messages):
        if i == len(messages) - 1:
            await message.answer(
                text,
                reply_markup=get_admin_keyboard(),
            )
        else:
            await message.answer(text)



@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return

    await state.clear()
    await message.answer(
        "Адмін-панель відкрита.",
        reply_markup=get_admin_keyboard(),
    )


@router.message(lambda message: message.text == "Додати книгу")
async def start_add_book(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
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
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
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
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return
    description = (message.text or "").strip()

    if not description:
        await message.answer("Опис книги не може бути порожнім. Спробуйте ще раз.")
        return

    data = await state.get_data()
    title = data.get("title")

    if not title:
        await state.clear()
        await message.answer("Сталася помилка стану. Почніть додавання книги ще раз.")
        return

    book = await create_book_service(
        session=session,
        title=title,
        description=description,
    )

    await state.clear()

    deep_link = build_book_deep_link(book.id)
    qr_buffer = generate_qr_code_with_book_id(
        data=deep_link,
        book_id=book.id,
    )
    qr_file = BufferedInputFile(
        file=qr_buffer.getvalue(),
        filename=f"book_{book.id}_qr.png",
    )
    
    await message.answer(
        "✅ Книгу успішно додано.\n\n"
        f"ID: {book.id}\n"
        f"Назва: {book.title}\n"
        f"Опис: {book.description}\n\n"
        f"Посилання для книги:\n{deep_link}",
        reply_markup=get_admin_keyboard(),
    )
    
    await message.answer_photo(
        photo=qr_file,
        caption=f"QR-код для книги ID {book.id}: «{book.title}»"
    )
    

@router.message(lambda message: message.text == "Керування книгами")
async def start_manage_books(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
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
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return

    book_id_raw = (message.text or "").strip()

    if not book_id_raw.isdigit():
        await message.answer("ID книги має бути цілим числом. Спробуйте ще раз.")
        return

    book_id = int(book_id_raw)

    book = await get_book_by_id_service(
        session=session,
        book_id=book_id,
    )

    if book is None:
        await message.answer("Книгу з таким ID не знайдено.")
        return

    await state.clear()

    await message.answer(
        await format_book_info(book, session),
        reply_markup=get_admin_book_actions_keyboard(book.id, is_taken=book.taken_by is not None),
    )


@router.callback_query(F.data.startswith("overall_edit_book:"))
async def process_edit_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
        return
    
    book_id_str = callback.data.removeprefix("overall_edit_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    book = await get_book_by_id_service(
        session=session,
        book_id=book_id,
    )

    if book is None:
        await callback.message.edit_text("Книгу не знайдено.")
        await callback.answer()
        return

    await state.clear()
    await state.update_data(edit_book_id=book_id)

    await callback.message.answer(
        "Що саме ви хочете змінити?",
        reply_markup=get_edit_book_fields_keyboard(book_id),
    )
    await callback.answer()
    

@router.callback_query(F.data.startswith("book_edit_menu:"))
async def process_edit_book_menu(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
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

        await callback.message.edit_text(
            await format_book_info(book, session),
            reply_markup=get_admin_book_actions_keyboard(book.id, is_taken=book.taken_by is not None),
        )
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
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
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
        await message.answer("Сталася помилка стану. Почніть редагування книги ще раз.")
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
        f"{await format_book_info(result, session)}",
        reply_markup=get_admin_keyboard(),
    )

@router.message(AdminManageBookStates.waiting_for_new_description)
async def process_new_book_description(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return

    new_description = (message.text or "").strip()

    if not new_description:
        await message.answer("Опис не може бути порожнім. Спробуйте ще раз.")
        return

    data = await state.get_data()
    book_id = data.get("edit_book_id")

    if book_id is None:
        await state.clear()
        await message.answer("Сталася помилка стану. Почніть редагування книги ще раз.")
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
        f"{await format_book_info(result, session)}",
        reply_markup=get_admin_keyboard(),
    )

@router.callback_query(F.data.startswith("delete_book:"))
async def process_delete_book_request(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
        return
    
    book_id_str = callback.data.removeprefix("delete_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    await callback.message.edit_reply_markup(
        reply_markup=get_delete_book_confirmation_keyboard(book_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_book:"))
async def process_confirm_delete_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
        return

    book_id_str = callback.data.removeprefix("confirm_delete_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    result = await delete_book_service(
        session=session,
        book_id=book_id,
    )

    if result == "success":
        await callback.message.edit_text("✅ Книгу успішно видалено.")
        await callback.message.answer(
            "Повертаю вас до адмін-панелі.",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    if result == "book_not_found":
        await callback.message.edit_text("❌ Книгу не знайдено.")
        await callback.message.answer(
            "Повертаю вас до адмін-панелі.",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    if result == "book_is_taken":
        await callback.message.edit_text("⚠️ Книгу не можна видалити, бо вона зараз на руках.")
        await callback.message.answer(
            "Повертаю вас до адмін-панелі.",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text("Сталася невідома помилка.")
    await callback.message.answer(
        "Повертаю вас до адмін-панелі.",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_delete_book:"))
async def process_cancel_delete_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
        return

    book_id_str = callback.data.removeprefix("cancel_delete_book:")

    if not book_id_str.isdigit():
        await callback.answer("Некоректний ID книги.", show_alert=True)
        return

    book_id = int(book_id_str)

    book = await get_book_by_id_service(
        session=session,
        book_id=book_id,
    )

    if book is None:
        await callback.message.edit_text("Книгу не знайдено.")
        await callback.message.answer(
            "Дію скасовано.",
            reply_markup=get_admin_keyboard(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        await format_book_info(book, session),
        reply_markup=get_admin_book_actions_keyboard(book.id),
    )
    await callback.message.answer(
        "Видалення скасовано.",
        reply_markup=get_admin_keyboard(),
    )
    await callback.answer()


@router.message(lambda message: message.text == "Користувачі")
async def list_users(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    user = await get_user_by_id_service(
        session=session,
        user_id=message.from_user.id,
    )

    if user is None or not await if_admin_user(session=session, user_id=user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return

    await state.clear()

    taken_books = await get_taken_books_service(session=session)
    blocks = await format_users_with_taken_books(session=session, books=taken_books)

    if isinstance(blocks, str):
        await message.answer(
            blocks,
            reply_markup=get_admin_keyboard(),
        )
        return

    messages = split_blocks_into_messages(blocks=blocks)

    for i, text in enumerate(messages):
        if i == len(messages) - 1:
            await message.answer(
                text,
                reply_markup=get_admin_keyboard(),
            )
        else:
            await message.answer(text)
            
            
@router.callback_query(F.data.startswith("force_return_book:"))
async def process_force_return_book(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
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
        await callback.answer("Книгу примусово повернуто.", show_alert=True)
        book = await get_book_by_id_service(
            session=session,
            book_id=book_id,
        )
        if book is not None:
            await callback.message.edit_text(
                "Оновлено інформацію про книгу після примусового повернення:\n\n",
                await format_book_info(book, session),
                reply_markup=get_admin_book_actions_keyboard(book.id, is_taken=book.taken_by is not None),
            )
        return

    await callback.answer("Сталася невідома помилка.", show_alert=True)
    
@router.callback_query(F.data.startswith("show_qr_code:"))
async def process_show_qr_code(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    if not await if_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.")
        return

    book_id_str = callback.data.removeprefix("show_qr_code:")

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

    deep_link = build_book_deep_link(book.id)
    qr_buffer = generate_qr_code_with_book_id(
        data=deep_link,
        book_id=book.id,
    )
    qr_file = BufferedInputFile(
        file=qr_buffer.getvalue(),
        filename=f"book_{book.id}_qr.png",
    )

    await callback.message.answer_photo(
        photo=qr_file,
        caption=f"QR-код для книги ID {book.id}: «{book.title}»\n\nПосилання для книги:\n{deep_link}"
    )
    await callback.answer()