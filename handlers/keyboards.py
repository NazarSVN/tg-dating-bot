from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

end_of_profiles_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📑 Дивитися анкети"), KeyboardButton(text="✏️ Заповнити анкету наново")],
        [KeyboardButton(text="👀 Хто мене лайкнув"), KeyboardButton(text="🙈 Скрити мою анкету")],
        [KeyboardButton(text="🌐 Змінити мову"), KeyboardButton(text="🆘 Підтримка")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


# Меню перегляду анкет
browse_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❤️ Лайк"), KeyboardButton(text="➡️ Пропустити")],
        [KeyboardButton(text="🚪 Вийти з перегляду")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)