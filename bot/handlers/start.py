from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_services import (
    get_user_by_id_service,
    create_user_or_get_existing,
    update_user_tg_username_service,
)
from services.book_service import (
    get_book_by_id_service,
    take_book_service,
    
)
from bot.states.registration import RegistrationStates
from bot.handlers.books import send_book_view
from bot.keyboards.reply import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username
    start_payload = command.args

    user = await get_user_by_id_service(
        session=session,
        user_id=telegram_id,
    )

    if user is not None:
        if user.tg_username != telegram_username:
            await update_user_tg_username_service(
                session=session,
                user_id=telegram_id,
                tg_username=telegram_username,
            )

        await state.clear()

        if start_payload:
            await handle_start_payload(
                message=message,
                payload=start_payload,
                session=session,
            )
            return

        await message.answer(f"З поверненням, {user.full_name} 📚")
        return

    await state.clear()

    if start_payload:
        await state.update_data(start_payload=start_payload)

    await state.set_state(RegistrationStates.waiting_for_full_name)
    await message.answer(
        "Вітаю! Для реєстрації введіть ваше ім'я та прізвище."
    )


@router.message(RegistrationStates.waiting_for_full_name)
async def process_full_name(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    full_name = (message.text or "").strip()

    if not full_name:
        await message.answer("Ім'я та прізвище не можуть бути порожніми. Спробуйте ще раз.")
        return

    if len(full_name) < 3:
        await message.answer("Надто коротке значення. Введіть ім'я та прізвище ще раз.")
        return

    existing_user = await get_user_by_id_service(
        session=session,
        user_id=message.from_user.id,
    )

    if existing_user is not None:
        await state.clear()
        await message.answer(f"Ви вже зареєстровані, {existing_user.full_name}.")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationStates.waiting_for_contact)
    await message.answer("Дякую! Тепер, будь ласка, надішліть ваш номер телефону.")


@router.message(RegistrationStates.waiting_for_contact)
async def process_contact(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
) -> None:
    contact = (message.text or "").strip()
    telegram_id = message.from_user.id
    telegram_username = message.from_user.username

    if not contact:
        await message.answer("Контактна інформація не може бути порожньою. Спробуйте ще раз.")
        return

    data = await state.get_data()
    full_name = data.get("full_name")
    start_payload = data.get("start_payload")

    if not full_name:
        await state.clear()
        await message.answer("Сталася помилка реєстрації. Спробуйте ще раз через /start.")
        return

    await create_user_or_get_existing(
        session=session,
        user_id=telegram_id,
        full_name=full_name,
        contact=contact,
        tg_username=telegram_username,
    )

    await state.clear()

    await message.answer(
        f"Реєстрацію завершено, {full_name} ✅\n"
        f"Ваш контакт: {contact} ✅",
        reply_markup=get_main_menu_keyboard(),
    )

    if start_payload:
        await handle_start_payload(
            message=message,
            payload=start_payload,
            session=session,
        )


async def handle_start_payload(
    message: Message,
    payload: str,
    session: AsyncSession,
) -> None:
    if payload.startswith("book_"):
        book_id_part = payload.removeprefix("book_")

        if not book_id_part.isdigit():
            await message.answer("Некоректне посилання на книгу.")
            return

        book_id = int(book_id_part)
        await send_book_view(
            message=message,
            session=session,
            user_id=message.from_user.id,
            book_id=book_id,
        )
        return

    await message.answer("Невідомий параметр запуску.")