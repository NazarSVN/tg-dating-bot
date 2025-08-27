from aiogram.fsm.state import State, StatesGroup

class Form(StatesGroup):
    age = State()
    gender = State()
    preference = State()
    location = State()
    phone = State()
    name = State()
    bio = State()
    photos = State()
    preview = State()  