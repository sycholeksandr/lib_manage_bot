from aiogram.fsm.state import State, StatesGroup


class AdminAddBookStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_author = State()
    waiting_for_publisher = State()
    waiting_for_genre = State()
    waiting_for_language = State()
    waiting_for_description = State()
    
class AdminManageBookStates(StatesGroup):
    waiting_for_book_id = State()
    waiting_for_new_title = State()
    waiting_for_new_author = State()
    waiting_for_new_publisher = State()
    waiting_for_new_genre = State()
    waiting_for_new_language = State()
    waiting_for_new_description = State()