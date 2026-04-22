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
    builder.button(text="Змінити автора", callback_data=f"book_edit_menu:author:{book_id}")
    builder.button(text="Змінити видавництво", callback_data=f"book_edit_menu:publisher:{book_id}")
    builder.button(text="Змінити жанр", callback_data=f"book_edit_menu:genre:{book_id}")
    builder.button(text="Змінити мову", callback_data=f"book_edit_menu:language:{book_id}")
    builder.button(text="Змінити опис", callback_data=f"book_edit_menu:description:{book_id}")
    builder.button(text="Скасувати", callback_data=f"book_edit_menu:cancel:{book_id}")
    builder.adjust(1)
    return builder.as_markup()

def get_books_catalog_keyboard(
    current_page: int,
    total_pages: int,
    filter_value: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    if current_page > 1:
        builder.button(
            text="⬅️ Назад",
            callback_data=f"books_page:{filter_value}:{current_page - 1}",
        )
    else:
        builder.button(
            text="⬅️ Назад", callback_data="noop"
        )
                
    builder.button(text=f"{current_page}/{total_pages}", callback_data="noop")
    
    if current_page < total_pages:
        builder.button(
            text="➡️ Далі",
            callback_data=f"books_page:{filter_value}:{current_page + 1}",
        )
    else:
        builder.button(
            text="➡️ Далі",
            callback_data="noop"
        )

    builder.adjust(3)
    return builder.as_markup()

def get_book_separation_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Доступні книги", callback_data="books_filter:available")
    builder.button(text="Книги на руках", callback_data="books_filter:taken")
    builder.button(text="Показати всі", callback_data="books_filter:all")
    builder.button(text="До адмін-панелі", callback_data="books_filter:back")
    builder.adjust(1)
    return builder.as_markup()