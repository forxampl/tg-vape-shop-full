from aiogram.fsm.state import StatesGroup, State

class StartStates(StatesGroup):
    confirm_age = State()
    choose_language = State()