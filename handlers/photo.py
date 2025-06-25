# handlers/photo.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile
from aiogram.fsm.context import FSMContext
from states import Form
import os
from config import TELEGRAM_TOKEN
from aiogram import Bot
from database.models import save_user

from database.models import (
    save_user,
    preload_profiles,  # ← ЭТО!
    get_next_profile,
    record_like,
    check_mutual_like
)

bot = Bot(token=TELEGRAM_TOKEN)
router = Router()

os.makedirs("media/users", exist_ok=True)

@router.message(Form.photos, F.content_type.in_({'photo', 'video'}))
async def handle_media(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    media_paths = data.get("photos", [])

    if len(media_paths) >= 3:
        await message.answer("📛 Максимум 3 фото. Натисни «це все, зберегти фото».")
        return

    # Скачиваем файл
    file = message.photo[-1] if message.photo else message.video
    file_info = await bot.get_file(file.file_id)
    file_ext = ".jpg" if message.photo else ".mp4"
    user_dir = f"media/users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    file_index = len(media_paths) + 1
    filename = f"photo{file_index}{file_ext}"
    file_path = os.path.join(user_dir, filename)
    await bot.download_file(file_info.file_path, file_path)

    media_paths.append(file_path)
    await state.update_data(photos=media_paths)

    await message.answer(
        f"✅ Додано {len(media_paths)} з 3. Можеш ще, або натисни «це все, зберегти фото».",
        reply_markup=InlineKeyboardBuilder()
        .button(text="✅ Це все, зберегти фото", callback_data="save_photos")
        .as_markup())

@router.callback_query(F.data == "use_profile_photo")
async def use_profile_photo(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    profile_photos = await bot.get_user_profile_photos(user_id)

    if not profile_photos.total_count:
        await callback.message.answer("У тебе немає фото профілю.")
        return

    photo = profile_photos.photos[0][0]
    file = await bot.get_file(photo.file_id)

    user_dir = f"media/users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, "profile.jpg")
    await bot.download_file(file.file_path, file_path)

    await state.update_data(photos=[file_path])
    await callback.message.answer("✅ Фото з профілю встановлено.")
    await show_profile_preview(callback.message, state)

@router.callback_query(F.data == "save_photos")
async def save_photos(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("photos"):
        await callback.message.answer("❗️ Треба додати хоча б одне фото.")
        return
    await show_profile_preview(callback.message, state)

async def show_profile_preview(message: Message, state: FSMContext):
    data = await state.get_data()

    name = data.get("name") or (message.from_user.first_name if hasattr(message.from_user, "first_name") else "Користувач")
    age = data.get("age")
    city = data.get("city")
    photos = data.get("photos", [])

    caption = f"*{name}*, {age}, {city}"

    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Так", callback_data="confirm_profile")
    builder.button(text="✏️ Змінити анкету", callback_data="edit_profile")
    builder.adjust(2)

    if photos and os.path.exists(photos[0]):
        photo_input = FSInputFile(photos[0])
        await message.answer_photo(photo=photo_input, caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await message.answer(text=caption, parse_mode="Markdown", reply_markup=builder.as_markup())


@router.callback_query(F.data == "edit_profile")
async def edit_profile(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    user_dir = f"media/users/{user_id}"
    if os.path.exists(user_dir):
        for f in os.listdir(user_dir):
            os.remove(os.path.join(user_dir, f))

    await state.update_data(photos=[])

    builder = InlineKeyboardBuilder()
    builder.button(text="Взяти з мого профілю телеграм", callback_data="use_profile_photo")

    await callback.message.answer(
        "📸 Надішли нові фото або відео (до 3), або натисни кнопку, щоб взяти з мого профілю телеграм.",
        reply_markup=builder.as_markup()
    )
    await state.set_state(Form.photos)

@router.callback_query(F.data == "edit_name")
async def edit_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введи нове ім’я:")
    await state.set_state(Form.name)

@router.callback_query(F.data == "restart")
async def restart(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Розпочинаємо заново! Введи /start щоб почати.")

@router.callback_query(F.data == "confirm_profile")
async def confirm_profile(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    save_user(callback.from_user.id, data)
    await callback.message.answer("🎉 Твій профіль підтверджено! Можеш починати знайомства.")
    await callback.message.delete()
    await state.clear()

    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Переглянути анкети", callback_data="browse_profiles")
    await callback.message.answer("Хочеш переглянути інших користувачів?", reply_markup=builder.as_markup())

@router.callback_query(F.data == "browse_profiles")
async def browse_profiles(callback: CallbackQuery):
    user_id = callback.from_user.id
    preload_profiles(user_id)
    await send_next_profile(callback.message, user_id)

@router.callback_query(F.data.startswith("like_"))
async def like_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    liked_id = int(callback.data.split("_")[1])
    record_like(user_id, liked_id)

    if check_mutual_like(user_id, liked_id):
        await callback.message.answer("🎉 У тебе новий збіг! Ви лайкнули один одного!")
    await send_next_profile(callback.message, user_id)

@router.callback_query(F.data == "next_profile")
async def next_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    await send_next_profile(callback.message, user_id)

async def send_next_profile(message: Message, user_id: int):
    profile = get_next_profile(user_id)
    if not profile:
        await message.answer("😕 Анкети закінчилися. Спробуй пізніше.")
        return

    caption = f"*{profile['name']}*, {profile['age']}, {profile['city']}\n{profile.get('bio', '')}"

    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ Лайк", callback_data=f"like_{profile['user_id']}")
    builder.button(text="➡️ Пропустити", callback_data="next_profile")
    builder.adjust(2)

    photos = profile.get("photos", [])
    if photos and os.path.exists(photos[0]):
        photo_input = FSInputFile(photos[0])
        await message.answer_photo(photo=photo_input, caption=caption, parse_mode="Markdown", reply_markup=builder.as_markup())
    else:
        await message.answer(caption, parse_mode="Markdown", reply_markup=builder.as_markup())
