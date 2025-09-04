import os
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from states import Form
from database.models import save_user, preload_profiles, get_next_profile, record_like, check_mutual_like
from handlers.profile import send_next_profile

router = Router()
os.makedirs("media/users", exist_ok=True)

# --- Меню ReplyKeyboard для профілю ---
profile_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❤️ Лайк"), KeyboardButton(text="➡️ Пропустити")],
        [KeyboardButton(text="✏️ Змінити анкету")],
        [KeyboardButton(text="Взяти з мого профілю телеграм")],
        [KeyboardButton(text="✅ Це все, зберегти фото")]
    ],
    resize_keyboard=True
)

# --- Завантаження фото ---
@router.message(Form.photos, F.content_type.in_({'photo', 'video'}))
async def handle_media(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    media_paths = data.get("photos", [])

    if len(media_paths) >= 3:
        await message.answer("📛 Максимум 3 фото. Натисни «✅ Це все, зберегти фото».", reply_markup=profile_menu)
        return

    file = message.photo[-1] if message.photo else message.video
    file_info = await message.bot.get_file(file.file_id)
    file_ext = ".jpg" if message.photo else ".mp4"
    user_dir = f"media/users/{user_id}"
    os.makedirs(user_dir, exist_ok=True)
    file_index = len(media_paths) + 1
    filename = f"photo{file_index}{file_ext}"
    file_path = os.path.join(user_dir, filename)
    await message.bot.download_file(file_info.file_path, file_path)

    media_paths.append(file_path)
    await state.update_data(photos=media_paths)
    await message.answer(f"✅ Додано {len(media_paths)} з 3. Можеш ще або натисни кнопку.", reply_markup=profile_menu)


# --- Попередній перегляд профілю ---
async def show_profile_preview(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data.get("name") or (message.from_user.first_name if hasattr(message.from_user, "first_name") else "Користувач")
    age = data.get("age")
    city = data.get("city")
    photos = data.get("photos", [])
    caption = f"*{name}*, {age}, {city}"

    if photos and os.path.exists(photos[0]):
        photo_input = FSInputFile(photos[0])
        await message.answer_photo(photo=photo_input, caption=caption, parse_mode="Markdown", reply_markup=profile_menu)
    else:
        await message.answer(caption, parse_mode="Markdown", reply_markup=profile_menu)


# --- Лайк профілю ---
@router.message(lambda m: m.text == "❤️ Лайк")
async def like_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    liked_user_id = data.get("current_profile_id")
    if not liked_user_id:
        await message.answer("Спочатку відкрий анкету 😉", reply_markup=profile_menu)
        return

    record_like(message.from_user.id, liked_user_id)

    # Отримуємо юзера з БД
    from database.models import get_user
    liked_user = get_user(liked_user_id)

    if liked_user:
        username = liked_user.get("username")
        name = liked_user.get("name", "Користувач")

        if username:
            link = f"[{name} (@{username})](https://t.me/{username})"
        else:
            link = f"[{name}](tg://user?id={liked_user_id})"
    else:
        link = f"[користувачем](tg://user?id={liked_user_id})"

    if check_mutual_like(message.from_user.id, liked_user_id):
        await message.answer(
            f"🎉 У тебе взаємний лайк з {link}!",
            reply_markup=profile_menu,
            parse_mode="Markdown"
        )
    else:
        await message.answer("Лайк поставлено ✅", reply_markup=profile_menu)

    next_profile_id = await send_next_profile(message, message.from_user.id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)

# --- Пропустити профіль ---
@router.message(lambda m: m.text == "➡️ Пропустити")
async def skip_profile(message: Message, state: FSMContext):
    next_profile_id = await send_next_profile(message, message.from_user.id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)


# --- Перегляд анкет ---
@router.message(lambda m: m.text == "📑 Дивитися анкети")
async def view_profiles(message: Message, state: FSMContext):
    next_profile_id = await send_next_profile(message, message.from_user.id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)


# --- Взяти фото з профілю Telegram ---
@router.message(lambda m: m.text == "Взяти з мого профілю телеграм")
async def use_profile_photo(message: Message, state: FSMContext):
    profile_photos = await message.bot.get_user_profile_photos(message.from_user.id)
    if not profile_photos.total_count:
        await message.answer("У тебе немає фото профілю.", reply_markup=profile_menu)
        return

    photo = profile_photos.photos[0][0]
    file = await message.bot.get_file(photo.file_id)
    user_dir = f"media/users/{message.from_user.id}"
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, "profile.jpg")
    await message.bot.download_file(file.file_path, file_path)

    await state.update_data(photos=[file_path])
    await message.answer("✅ Фото з профілю встановлено.", reply_markup=profile_menu)
    await show_profile_preview(message, state)


# --- Збереження фото ---
@router.message(lambda m: m.text == "✅ Це все, зберегти фото")
async def save_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("photos"):
        await message.answer("❗️ Треба додати хоча б одне фото.", reply_markup=profile_menu)
        return

    # ✅ зберігаємо у базу
    save_user(message.from_user.id, data)

    await show_profile_preview(message, state)
    await state.clear()  # можна очистити FSM, якщо анкету завершено

    from handlers.keyboards import end_of_profiles_menu
    await message.answer(
        "✅ Анкету збережено. Тепер можна дивитися інших користувачів 👇",
        reply_markup=end_of_profiles_menu
    )
# --- Редагування анкети ---
@router.message(lambda m: m.text == "✏️ Змінити анкету")
async def edit_profile(message: Message, state: FSMContext):
    user_dir = f"media/users/{message.from_user.id}"
    if os.path.exists(user_dir):
        for f in os.listdir(user_dir):
            os.remove(os.path.join(user_dir, f))
    await state.update_data(photos=[])
    await message.answer("📸 Надішли нові фото або відео (до 3), або натисни кнопку «Взяти з мого профілю телеграм».", reply_markup=profile_menu)
    await state.set_state(Form.photos)

# --- Підтвердження анкети ---
@router.message(lambda m: m.text == "✅ Так")
async def confirm_profile(message: Message, state: FSMContext):
    data = await state.get_data()
    save_user(message.from_user.id, data)
    await state.clear()
    from handlers.keyboards import end_of_profiles_menu
    await message.answer("🎉 Твій профіль підтверджено! Можеш починати знайомства.", reply_markup=end_of_profiles_menu)

