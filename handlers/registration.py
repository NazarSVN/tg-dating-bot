# handlers/registration.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from states import Form
from utils.location import validate_city

router = Router()

@router.callback_query(F.data == "agree")
async def ask_age(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Скільки тобі років? (від 14 до 60)")
    await state.set_state(Form.age)

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
    builder = InlineKeyboardBuilder()
    builder.button(text="👧 Я дівчина", callback_data="gender_girl")
    builder.button(text="👦 Я хлопець", callback_data="gender_boy")
    builder.adjust(1)
    await message.answer("Хто ти?", reply_markup=builder.as_markup())
    await state.set_state(Form.gender)

@router.callback_query(Form.gender)
async def handle_gender(callback: CallbackQuery, state: FSMContext):
    gender = callback.data.split('_')[1]
    await state.update_data(gender=gender)
    builder = InlineKeyboardBuilder()
    builder.button(text="👧 Дівчата", callback_data="like_girls")
    builder.button(text="👦 Хлопці", callback_data="like_boys")
    builder.button(text="🤝 Все одно", callback_data="like_all")
    builder.adjust(1)
    await callback.message.edit_text("Хто тобі подобається?", reply_markup=builder.as_markup())
    await state.set_state(Form.preference)

@router.callback_query(Form.preference)
async def handle_preference(callback: CallbackQuery, state: FSMContext):
    preference = callback.data.split('_')[1]
    await state.update_data(preference=preference)
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Відправити моє місце розташування", request_location=True)]],
        resize_keyboard=True, one_time_keyboard=True)
    await callback.message.answer("З якого ти міста? Натисни кнопку або введи вручну:", reply_markup=kb)
    await state.set_state(Form.location)

@router.message(Form.location)
async def handle_location(message: Message, state: FSMContext):
    if message.location:
        lat, lon = message.location.latitude, message.location.longitude
        await state.update_data(city=f"Координати: {lat:.4f}, {lon:.4f}")
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
        resize_keyboard=True, one_time_keyboard=True)
    await message.answer(
        "Мені потрібен твій номер телефону для підтвердження анкети. Інші користувачі його не побачать.",
        reply_markup=kb
    )
    await state.set_state(Form.phone)

@router.message(Form.phone)
async def handle_phone(message: Message, state: FSMContext):
    if not message.contact:
        await message.answer("📞 Натисни кнопку для надсилання номера телефону.")
        return
    await state.update_data(phone=message.contact.phone_number)
    data = await state.get_data()
    name = data.get("name") or message.from_user.first_name

    builder = InlineKeyboardBuilder()
    builder.button(text=f"🙋 Звати {name}", callback_data="name_profile")
    builder.adjust(1)

    await message.answer("Як до тебе звертатися?", reply_markup=builder.as_markup())
    await message.answer("⬆️ Натисни кнопку або введи ім’я вручну.", reply_markup=ReplyKeyboardRemove())
    await state.set_state(Form.name)

@router.callback_query(F.data == "name_profile")
async def use_profile_name(callback: CallbackQuery, state: FSMContext):
    await state.update_data(name=callback.from_user.first_name)
    await ask_bio(callback.message, state)

@router.message(Form.name)
async def handle_custom_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Введи повноцінне ім’я.")
        return
    await state.update_data(name=name)
    await ask_bio(message, state)

async def ask_bio(message: Message, state: FSMContext):
    skip_button = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Пропустити")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "📝 Розкажи про себе, кого хочеш знайти, чим пропонуєш зайнятись.",
        reply_markup=skip_button
    )
    await state.set_state(Form.bio)

@router.message(Form.bio)
async def handle_bio(message: Message, state: FSMContext):
    bio = message.text.strip()
    if bio.lower() != "пропустити":
        await state.update_data(bio=bio)
    else:
        await state.update_data(bio="")
    await message.answer(
        "📸 Тепер надішли фото або запиши відео 👍 (до 15 сек)",
        reply_markup=InlineKeyboardBuilder()
        .button(text="Взяти з мого профілю телеграм", callback_data="use_profile_photo")
        .as_markup()
    )
    await state.update_data(photos=[])
    await state.set_state(Form.photos)
