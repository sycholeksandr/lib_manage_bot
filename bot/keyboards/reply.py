from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        KeyboardButton(text="📚 Показати всі книги"),
        KeyboardButton(text="📖 Книги у мене"),
    ]

    keyboard = ReplyKeyboardMarkup(
        keyboard=[buttons],
        resize_keyboard=True,
    )

    return keyboard

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Додати книгу"),
                KeyboardButton(text="Керування книгами"),
            ],
            [
                KeyboardButton(text="Користувачі"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()