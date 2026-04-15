from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_take_book_confirmation_keyboard(book_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="Так", callback_data=f"take_book:{book_id}")
    builder.button(text="Ні", callback_data=f"cancel_book_action:{book_id}")

    builder.adjust(2)
    return builder.as_markup()


def get_return_book_confirmation_keyboard(book_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.button(text="Так", callback_data=f"return_book:{book_id}")
    builder.button(text="Ні", callback_data=f"cancel_book_action:{book_id}")

    builder.adjust(2)
    return builder.as_markup()


def get_admin_book_actions_keyboard(book_id: int, is_taken: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Редагувати", callback_data=f"overall_edit_book:{book_id}")
    if is_taken:
        builder.button(text="Примусово повернути", callback_data=f"force_return_book:{book_id}")
    builder.button(text="Показати QR-код", callback_data=f"show_qr_code:{book_id}")
    builder.button(text="Видалити", callback_data=f"delete_book:{book_id}")
    builder.button(text="Скасувати", callback_data=f"cancel_book_action:{book_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_delete_book_confirmation_keyboard(book_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Так, видалити", callback_data=f"confirm_delete_book:{book_id}")
    builder.button(text="Скасувати", callback_data=f"cancel_delete_book:{book_id}")
    builder.adjust(1)
    return builder.as_markup()


def get_edit_book_fields_keyboard(book_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Змінити назву", callback_data=f"book_edit_menu:title:{book_id}")
    builder.button(text="Змінити опис", callback_data=f"book_edit_menu:description:{book_id}")
    builder.button(text="Скасувати", callback_data=f"book_edit_menu:cancel:{book_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_books_catalog_keyboard(
    current_page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if current_page > 1:
        builder.button(
            text="⬅️ Назад",
            callback_data=f"books_page:{current_page - 1}",
        )

    if current_page < total_pages:
        builder.button(
            text="➡️ Далі",
            callback_data=f"books_page:{current_page + 1}",
        )

    builder.adjust(2)
    return builder.as_markup()