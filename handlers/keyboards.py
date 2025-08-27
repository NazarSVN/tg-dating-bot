from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

end_of_profiles_menu = ReplyKeyboardMarkup(
    keyboard=[  
        [KeyboardButton(text="📑 Дивитися анкети")],
        [KeyboardButton(text="✏️ Заповнити анкету наново")],
        [KeyboardButton(text="👀 Хто мене лайкнув")],
        [KeyboardButton(text="❤️ Лайк"), KeyboardButton(text="➡️ Пропустити")],
        [KeyboardButton(text="✅ Це все, зберегти фото"), KeyboardButton(text="✏️ Змінити анкету")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)
