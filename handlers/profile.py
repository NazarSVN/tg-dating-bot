import os
from aiogram import Router
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from database.models import get_next_profile, preload_profiles
from handlers.keyboards import end_of_profiles_menu, browse_menu
from aiogram.types import ReplyKeyboardRemove
from aiogram import F

router = Router()

async def show_profile_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name", "Не вказано")
    age = data.get("age", "Не вказано")
    gender = data.get("gender", "Не вказано")
    preference = data.get("preference", "Не вказано")
    city = data.get("city", "Не вказано")
    bio = data.get("bio", "Не вказано")
    photos = data.get("photos", [])

    text = (
        f"📋 Перевір свою анкету:\n\n"
        f"👤 Ім'я: {name}\n"
        f"🎂 Вік: {age}\n"
        f"⚧ Стать: {gender}\n"
        f"💖 Хто подобається: {preference}\n"
        f"📍 Місто: {city}\n"
        f"📝 Bio: {bio}\n"
        f"📸 Фото: {len(photos)} шт."
    )
    await message.answer(text)

    for photo_path in photos:
        if os.path.exists(photo_path):
            file = FSInputFile(photo_path)
            await message.answer_photo(file)
        else:
            await message.answer(f"❌ Не вдалося знайти файл: {photo_path}")

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Це все, зберегти")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("Якщо все вірно, натисни кнопку нижче:", reply_markup=kb)


async def send_next_profile(message: Message, user_id: int) -> int | None:
    from database.models import _browse_cache, _browse_index
    
    await message.answer("🔄 Завантаження наступного профілю...", reply_markup=ReplyKeyboardRemove())

    if not _browse_cache.get(user_id) or _browse_index.get(user_id, 0) >= len(_browse_cache.get(user_id, [])):
        profiles = preload_profiles(user_id)
        if not profiles:
            _browse_cache[user_id] = [] 
            _browse_index[user_id] = 0
            await message.answer("😕 Анкети закінчилися.", reply_markup=end_of_profiles_menu)
            return None

    profile = get_next_profile(user_id)
    if not profile:
        _browse_cache[user_id] = []
        _browse_index[user_id] = 0
        await message.answer("😕 Анкети закінчилися.", reply_markup=end_of_profiles_menu)
        return None

    caption = f"*{profile['name']}*, {profile['age']}, {profile['city']}\n{profile.get('bio', '')}"

    photos = profile.get("photos", [])
    if photos and os.path.exists(photos[0]):
        photo_input = FSInputFile(photos[0])
        await message.answer_photo(
            photo=photo_input,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=browse_menu
        )
    else:
        await message.answer(
            caption,
            parse_mode="Markdown",
            reply_markup=browse_menu
        )

    return profile["user_id"]

@router.message(F.text.contains("Вийти з перегляду"))
async def exit_browsing(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Ви вийшли з перегляду анкет ✅",
        reply_markup=end_of_profiles_menu  # або ReplyKeyboardRemove() якщо хочеш просто сховати
    )
