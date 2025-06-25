# keyboards/default.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def location_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Відправити моє місце розташування", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Надіслати мій номер телефону", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def skip_bio_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустити")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
