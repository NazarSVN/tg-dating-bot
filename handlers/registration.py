from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from states import Form
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.location import validate_city  
from handlers.profile import show_profile_preview
from database.models import save_user
from handlers.profile import send_next_profile
from utils.location import coords_to_city

import os

router = Router()

photo_registration_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📷 Взяти з мого профілю", callback_data="use_profile_photo")]
    ]
)

# --- Старт реєстрації ---
async def start_registration(message: Message, state: FSMContext):
    if not message.from_user.username:
        await message.answer(
            "❌ У тебе не встановлений @username у Telegram.\n\n"
            "Будь ласка, додай його в налаштуваннях Telegram і спробуй ще раз."
        )
        return
    
    await message.answer("Скільки тобі років? (від 14 до 60)", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.age)

@router.message(lambda m: m.text == "✅ Це все, зберегти")
async def save_profile(message: Message, state: FSMContext):
    if not message.from_user.username:
        await message.answer(
            "❌ У тебе не встановлений @username у Telegram.\n\n"
            "Будь ласка, додай його в налаштуваннях Telegram і пройди реєстрацію ще раз."
        )
        return

    data = await state.get_data()
    data["username"] = message.from_user.username   
    save_user(message.from_user.id, data)           
    
    await state.clear()

    await message.answer(
        "✅ Твоя анкета успішно збережена!\n"
        "Тепер можеш переглядати анкети інших користувачів."
    )
    next_profile_id = await send_next_profile(message, message.from_user.id)

    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)



@router.message(Form.age)
async def handle_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Введи, будь ласка, число.")
        return
    age = int(message.text)
    if not 14 <= age <= 60:
        await message.answer("😕 Вік має бути від 14 до 60 років.")
        return
    await state.update_data(age=age)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👧 Я дівчина"), KeyboardButton(text="👦 Я хлопець")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Хто ти?", reply_markup=kb)
    await state.set_state(Form.gender)

@router.message(Form.gender)
async def handle_gender(message: Message, state: FSMContext):
    text = message.text
    if text not in ["👧 Я дівчина", "👦 Я хлопець"]:
        await message.answer("Вибери, будь ласка, одну з кнопок.")
        return
    gender = "girl" if text == "👧 Я дівчина" else "boy"
    await state.update_data(gender=gender)

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👧 Дівчата")],
            [KeyboardButton(text="👦 Хлопці")],
            [KeyboardButton(text="🤝 Все одно")]
        ],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Хто тобі подобається?", reply_markup=kb)
    await state.set_state(Form.preference)

@router.message(Form.preference)
async def handle_preference(message: Message, state: FSMContext):
    text = message.text
    if text not in ["👧 Дівчата", "👦 Хлопці", "🤝 Все одно"]:
        await message.answer("Вибери, будь ласка, одну з кнопок.")
        return
    preference = text.split()[0].lower() if text != "🤝 Все одно" else "all"
    await state.update_data(preference=preference)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Відправити моє місце розташування", request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("З якого ти міста? Натисни кнопку або введи вручну:", reply_markup=kb)
    await state.set_state(Form.location)

@router.message(Form.location)
async def handle_location(message: Message, state: FSMContext):
    if message.location:
        lat, lon = message.location.latitude, message.location.longitude
        city = coords_to_city(lat, lon)
        if not city:
            await message.answer("❌ Не вдалося визначити місто. Спробуй ще раз або введи вручну.")
            return
        await state.update_data(city=city)
    else:
        city_raw = message.text.strip()
        if not city_raw or len(city_raw) < 2:
            await message.answer("❗️ Введи, будь ласка, назву міста.")
            return
        city = await validate_city(city_raw)
        if city is None:
            await message.answer("❌ Не вдалося знайти таке місто або сталася помилка. Спробуй ще раз.")
            return
        await state.update_data(city=city)

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Надіслати мій номер телефону", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer(
        f"📍 Твоє місто визначено як: *{city}*\n\n"
        "Тепер надішли номер телефону для підтвердження анкети.",
        parse_mode="Markdown",
        reply_markup=kb
    )
    await state.set_state(Form.phone)


@router.message(Form.phone)
async def handle_phone(message: Message, state: FSMContext):
    if not message.contact:
        await message.answer("📞 Натисни кнопку для надсилання номера телефону.")
        return
    await state.update_data(phone=message.contact.phone_number)

    await message.answer("Як до тебе звертатися? Введи ім'я:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)

# --- обробка імені ---
@router.message(Form.name)
async def handle_custom_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Введи повноцінне ім’я або натисни кнопку для використання імені з профілю.")
        return
    await state.update_data(name=name)

    # після введення імені пропонуємо біо
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустити")]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("📝 Розкажи про себе, кого хочеш знайти, чим пропонуєш зайнятись.", reply_markup=kb)
    await state.set_state(Form.bio)

@router.callback_query(F.data == "use_profile_name")
async def use_name_from_profile(callback: CallbackQuery, state: FSMContext):
    await state.update_data(name=callback.from_user.first_name)
    await ask_bio(callback.message, state)

async def ask_bio(message: Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустити")]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("📝 Розкажи про себе, кого хочеш знайти, чим пропонуєш зайнятись.", reply_markup=kb)
    await state.set_state(Form.bio)


# --- обробка біо ---
# --- після заповнення біо ---
@router.message(Form.bio)
async def handle_bio(message: Message, state: FSMContext):
    bio = message.text.strip()
    if bio.lower() != "пропустити":
        await state.update_data(bio=bio)
    else:
        await state.update_data(bio="")

    builder = InlineKeyboardBuilder()
    builder.button(text="📸 Надіслати фото/відео", callback_data="send_media")
    builder.button(text="📷 Взяти з мого профілю Telegram", callback_data="use_profile_photo")
    builder.adjust(1)

    await message.answer(
        "Тепер додай своє фото або відео (до 15 сек), або бери з профілю Telegram.",
        reply_markup=photo_registration_kb
    )
    await state.update_data(photos=[])
    await state.set_state(Form.photos)

@router.callback_query(F.data == "send_media")
async def handle_send_media(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Надішли фото або відео (до 15 сек). Або встанови з профілю (нижча якість)")
    await state.set_state(Form.photos)

@router.callback_query(F.data == "use_profile_photo")
async def handle_use_profile_photo(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_photos = await callback.bot.get_user_profile_photos(user_id)

    if not profile_photos.total_count:
        await callback.message.answer("❌ У тебе немає фото профілю.")
        return

    photo = profile_photos.photos[0][-1]
    file = await callback.bot.get_file(photo.file_id)

    user_dir = f"media/users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, "profile_photo.jpg")

    await callback.bot.download_file(file.file_path, file_path)

    await state.update_data(photos=[file_path])

    await callback.message.answer("✅ Фото з профілю встановлено.")

    # показуємо попередній перегляд анкети
    await show_profile_preview(callback.message, state)

    # після цього ставимо стан на preview
    await state.set_state(Form.preview)

@router.callback_query(Form.preview)
async def handle_profile_preview_actions(callback: CallbackQuery, state: FSMContext):
    if callback.data == "confirm_profile":
        await callback.message.answer("🎉 Анкета підтверджена!")
        # можеш змінити стан на кінцевий або clear()
        await state.clear()
    elif callback.data == "edit_profile":
        await callback.message.answer("✏️ Давай редагувати анкету.")
        await state.set_state(Form.age)  # або куди хочеш відправити

async def use_profile_photo(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_photos = await callback.bot.get_user_profile_photos(user_id)
    
    if not profile_photos.total_count:
        await callback.message.answer("❌ У тебе немає фото профілю.")
        return

    photo = profile_photos.photos[0][0]
    file = await callback.bot.get_file(photo.file_id)

    user_dir = f"media/users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, "profile_photo.jpg")

    await callback.bot.download(file, destination=file_path)

    await state.update_data(photos=[file_path])

    await callback.message.answer("✅ Фото з профілю встановлено.")
    
    from handlers.profile import show_profile_preview 
    await show_profile_preview(callback.message, state)