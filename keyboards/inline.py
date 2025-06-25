# keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder


def start_button() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Запустити", callback_data="launch_bot")
    return builder

def language_buttons() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    languages = ["Українська 🇺🇦", "English 🇬🇧", "Deutsch 🇩🇪", "Español 🇪🇸",
                 "Français 🇫🇷", "Italiano 🇮🇹", "Polski 🇵🇱", "Türkçe 🇹🇷"]
    for lang in languages:
        builder.button(text=lang, callback_data=f"lang_{lang}")
    builder.adjust(1)
    return builder

def lets_start_button() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="👉 ДАВАЙ ПОЧНЕМО", callback_data="lets_start")
    return builder

def agree_button() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ОКЕЙ", callback_data="agree")
    return builder

def gender_buttons() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="👧 Я дівчина", callback_data="gender_girl")
    builder.button(text="👦 Я хлопець", callback_data="gender_boy")
    builder.adjust(1)
    return builder

def preference_buttons() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="👧 Дівчата", callback_data="like_girls")
    builder.button(text="👦 Хлопці", callback_data="like_boys")
    builder.button(text="🤝 Все одно", callback_data="like_all")
    builder.adjust(1)
    return builder

def name_button(name: str) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text=f"🙋 Звати {name}", callback_data="name_profile")
    return builder

def photo_choice_button() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="Взяти з мого профілю телеграм", callback_data="use_profile_photo")
    return builder

def confirm_edit_buttons() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data="confirm_profile")
    builder.button(text="✏️ Змінити анкету", callback_data="edit_profile")
    builder.adjust(2)
    return builder


