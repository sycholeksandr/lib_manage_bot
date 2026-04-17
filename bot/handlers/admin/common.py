from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings

from bot.keyboards.inline import get_admin_book_actions_keyboard
from bot.keyboards.reply import get_admin_keyboard
from services.book_service import get_all_books_service
from services.qr_service import generate_qr_code_with_book_id
from services.user_services import get_user_by_id_service

router = Router()

MAX_MESSAGE_LENGTH = 4000
DESCRIPTION_PREVIEW_LENGTH = 30
BLOCK_SEPARATOR = "\n----------------------\n"


def build_book_deep_link(book_id: int) -> str:
    return f"https://t.me/{settings.TELEGRAM_BOT_NAME}?start=book_{book_id}"


def truncate_text(text: str | None, max_length: int = DESCRIPTION_PREVIEW_LENGTH) -> str:
    if not text:
        return "Опис відсутній."
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


async def is_admin_user(session: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id_service(session=session, user_id=user_id)
    return user is not None and user.is_admin


async def ensure_admin_message_access(
    message: Message,
    session: AsyncSession,
) -> bool:
    if not await is_admin_user(session=session, user_id=message.from_user.id):
        await message.answer("У вас немає доступу до цієї дії.")
        return False
    return True


async def ensure_admin_callback_access(
    callback: CallbackQuery,
    session: AsyncSession,
) -> bool:
    if not await is_admin_user(session=session, user_id=callback.from_user.id):
        await callback.answer("У вас немає доступу до цієї дії.", show_alert=True)
        return False
    return True


async def format_book_info(book, session: AsyncSession) -> str:
    taken_at_str = book.taken_at.strftime("%d.%m.%Y") if book.taken_at else "—"
    short_description = truncate_text(book.description)

    status = "доступна"
    taken_by_str = "—"
    telegram_line = ""

    if book.taken_by is not None:
        status = "на руках"
        user = await get_user_by_id_service(session=session, user_id=book.taken_by)
        taken_by_str = (
            user.full_name if user else f"Невідомий користувач (ID: {book.taken_by})"
        )
        if user and user.tg_username:
            telegram_line = (
                f'<b>Telegram:</b> '
                f'<a href="https://t.me/{user.tg_username}">@{user.tg_username}</a>\n'
            )

    return (
        f"📖 <b>ID:</b> {book.id}\n"
        f"<b>Назва:</b> {book.title}\n"
        f"<b>Автор:</b> {book.author or '—'}\n"
        f"<b>Видавництво:</b> {book.publisher or '—'}\n"
        f"<b>Жанр:</b> {book.genre or '—'}\n"
        f"<b>Мова:</b> {book.language or '—'}\n"
        f"<b>Опис:</b> {short_description}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Взята:</b> {taken_by_str}\n"
        f"{telegram_line}"
        f"<b>Дата взяття:</b> {taken_at_str}"
    )


def split_blocks_into_messages(
    blocks: list[str],
    max_length: int = MAX_MESSAGE_LENGTH,
) -> list[str]:
    messages: list[str] = []
    current_message = ""

    for block in blocks:
        if not current_message:
            current_message = block
            continue

        candidate = current_message + BLOCK_SEPARATOR + block
        if len(candidate) <= max_length:
            current_message = candidate
        else:
            messages.append(current_message)
            current_message = block

    if current_message:
        messages.append(current_message)

    return messages


async def build_users_with_taken_books_blocks(
    session: AsyncSession,
    books: list,
) -> list[str] | str:
    if not books:
        return "Зараз немає користувачів, у яких книги на руках."

    grouped: dict[int, list] = {}

    for book in books:
        if book.taken_by is None:
            continue
        grouped.setdefault(book.taken_by, []).append(book)

    blocks: list[str] = []

    for user_id, user_books in grouped.items():
        user = await get_user_by_id_service(session=session, user_id=user_id)
        if user is None:
            continue

        lines = [
            f"👤 <b>{user.full_name}</b>",
            f"<b>Телефон:</b> {user.contact or '—'}",
        ]

        if user.tg_username:
            lines.append(
                f'<b>Telegram:</b> '
                f'<a href="https://t.me/{user.tg_username}">@{user.tg_username}</a>'
            )

        lines.append("<b>Книги на руках:</b>")

        for book in user_books:
            taken_at_str = book.taken_at.strftime("%d.%m.%Y") if book.taken_at else "—"
            author_part = f" — {book.author}" if book.author else ""
            lines.append(
                f"• ID {book.id} — {book.title}{author_part} ({taken_at_str})"
            )

        blocks.append("\n".join(lines))

    if not blocks:
        return "Зараз немає коректних даних про користувачів з книгами на руках."

    return blocks


async def send_chunked_messages(
    message: Message,
    blocks: list[str] | str,
) -> None:
    if isinstance(blocks, str):
        await message.answer(blocks, reply_markup=get_admin_keyboard())
        return

    messages = split_blocks_into_messages(blocks=blocks)

    for index, text in enumerate(messages):
        if index == len(messages) - 1:
            await message.answer(text, reply_markup=get_admin_keyboard())
        else:
            await message.answer(text)


async def send_book_card(
    message: Message,
    session: AsyncSession,
    book,
) -> None:
    await message.answer(
        await format_book_info(book, session),
        reply_markup=get_admin_book_actions_keyboard(
            book.id,
            is_taken=book.taken_by is not None,
        ),
    )


async def send_book_card_from_callback(
    callback: CallbackQuery,
    session: AsyncSession,
    book,
) -> None:
    await callback.message.edit_text(
        await format_book_info(book, session),
        reply_markup=get_admin_book_actions_keyboard(
            book.id,
            is_taken=book.taken_by is not None,
        ),
    )


async def send_book_qr(
    message: Message,
    book,
) -> None:
    deep_link = build_book_deep_link(book.id)
    qr_buffer = generate_qr_code_with_book_id(
        data=deep_link,
        book_id=book.id,
    )
    qr_file = BufferedInputFile(
        file=qr_buffer.getvalue(),
        filename=f"book_{book.id}_qr.png",
    )

    caption_parts = [
        f'QR-код для книги ID {book.id}: «{book.title}»'
    ]

    if book.author:
        caption_parts.append(f"Автор: {book.author}")

    caption_parts.append("")
    caption_parts.append(f"Посилання для книги:\n{deep_link}")

    await message.answer_photo(
        photo=qr_file,
        caption="\n".join(caption_parts),
    )


@router.message(Command("admin"))
async def cmd_admin(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    await state.clear()
    await message.answer(
        "Адмін-панель відкрита.",
        reply_markup=get_admin_keyboard(),
    )


@router.message(Command("cancel"))
async def cancel_current_action(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "Наразі немає активної дії для скасування.",
            reply_markup=get_admin_keyboard(),
        )
        return

    await state.clear()
    await message.answer(
        "Поточну дію скасовано.",
        reply_markup=get_admin_keyboard(),
    )


@router.message(Command("all_books"))
async def cmd_all_books(
    message: Message,
    session: AsyncSession,
) -> None:
    if not await ensure_admin_message_access(message, session):
        return

    books = await get_all_books_service(session=session)
    if not books:
        await message.answer("Книг не знайдено.", reply_markup=get_admin_keyboard())
        return

    book_blocks = [await format_book_info(book, session) for book in books]
    await send_chunked_messages(message, book_blocks)