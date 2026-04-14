from aiogram.fsm.state import State, StatesGroup


class AdminAddBookStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_book_id = State()
    
class AdminManageBookStates(StatesGroup):
    waiting_for_book_id = State()
    waiting_for_new_title = State()
    waiting_for_new_description = State()