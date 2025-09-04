from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from states import Form
from .profile import send_next_profile
from database.models import record_like, check_mutual_like
from handlers.keyboards import end_of_profiles_menu
from database.models import get_connection
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

# Кнопка для очищення лайків
def who_liked_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Очистити всі лайки", callback_data="clear_likes")]
        ]
    )

# /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    # Дізнаємося статус користувача
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_hidden FROM users WHERE user_id = ?", (message.from_user.id,))
    row = cursor.fetchone()
    is_hidden = row[0] if row else 0
    conn.close()

    await message.answer("Вибери дію:", reply_markup=hide_show_menu(is_hidden))

# Дивитися анкети
@router.message(lambda m: m.text == "📑 Дивитися анкети")
async def view_profiles(message: types.Message, state: FSMContext):
    next_profile_id = await send_next_profile(message, message.from_user.id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)

# Заповнити анкету наново
@router.message(lambda m: m.text == "✏️ Заповнити анкету наново")
async def fill_again(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Form.age)
    await message.answer("Давай заповнимо анкету заново 🙂\nСкільки тобі років?")

from aiogram import types
from aiogram.types import FSInputFile
import json, os
from database.models import get_connection

# 👀 Хто мене лайкнув
@router.message(lambda m: m.text == "👀 Хто мене лайкнув")
async def who_liked(message: types.Message):
    user_id = message.from_user.id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT users.user_id, users.name, users.photos FROM likes
        JOIN users ON likes.liker_id = users.user_id
        WHERE likes.liked_id = ?
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("Ніхто ще тебе не лайкнув 😢")
        return

    for row in rows:
        liker_id, name, photos_json = row
        photos = []
        if photos_json:
            try:
                photos = json.loads(photos_json)
            except:
                photos = []

        media = []
        for photo_path in photos:
            if os.path.exists(photo_path):
                media.append(InputMediaPhoto(media=FSInputFile(photo_path)))
        if media:
            await message.answer_media_group(media=media)
    
        await message.answer(
            f"❤️ {name}\n 👉👉 tg://user?id={liker_id} \n ⚠️ Якщо користувач обмежив приватність, то посилання може не працювати"
        )

    # додаємо кнопку очищення
    await message.answer("Що зробити далі?", reply_markup=who_liked_menu())


# Лайк профілю
@router.message(lambda m: m.text == "❤️ Лайк")
async def like_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    liked_user_id = data.get("current_profile_id")
    liker_id = message.from_user.id

    if not liked_user_id:
        await message.answer("Спочатку відкрий анкету 😉")
        return

    record_like(liker_id, liked_user_id)

    # Отримуємо користувача з БД
    from database.models import get_user
    liked_user = get_user(liked_user_id)

    if liked_user:
        username = liked_user.get("username")
        name = liked_user.get("name", "Користувач")

        if username:
            # 👇 буде формат: Ім'я (@username) з клікабельним посиланням
            link = f"[{name} (@{username})](https://t.me/{username})"
        else:
            # fallback на ім'я + id
            link = f"{name} [tg://user?id={liked_user_id}]"
    else:
        link = f"[користувачем](tg://user?id={liked_user_id})"

    if check_mutual_like(liker_id, liked_user_id):
        await message.answer(
            f"🎉 Ура! У тебе взаємний лайк з {link}!",
            parse_mode="Markdown"
        )
    else:
        await message.answer("Лайк поставлено ✅")

    # Показуємо наступну анкету
    next_profile_id = await send_next_profile(message, liker_id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)
    else:
        await message.answer("Анкет більше немає 😢", reply_markup=end_of_profiles_menu)

# Пропустити профіль
@router.message(lambda m: m.text == "➡️ Пропустити")
async def skip_profile(message: types.Message, state: FSMContext):
    next_profile_id = await send_next_profile(message, message.from_user.id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)

# 🗑 Очистка лайків
@router.callback_query(lambda c: c.data == "clear_likes")
async def clear_likes(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    conn = get_connection()
    cursor = conn.cursor()

    # Видаляємо всі записи, де юзер лайкнув або його лайкнули
    cursor.execute('DELETE FROM likes WHERE liker_id = ? OR liked_id = ?', (user_id, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer("✅ Усі лайки очищені.")
    await callback.answer()

# Динамічне меню приховування/показу анкети
def hide_show_menu(is_hidden: bool):
    text = "👁 Показати мою анкету" if is_hidden else "🙈 Скрити мою анкету"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text)],
            [KeyboardButton(text="📑 Дивитися анкети")],
            [KeyboardButton(text="✏️ Заповнити анкету наново")],
            [KeyboardButton(text="👀 Хто мене лайкнув")],
            [KeyboardButton(text="🌐 Змінити мову")],
            [KeyboardButton(text="🆘 Підтримка")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

@router.message(lambda m: m.text in ["🙈 Скрити мою анкету", "👁 Показати мою анкету"])
async def toggle_profile_visibility(message: types.Message):
    user_id = message.from_user.id
    conn = get_connection()
    cursor = conn.cursor()

    # Дізнаємося поточний статус
    cursor.execute("SELECT is_hidden FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        is_hidden = row[0]
        new_status = 0 if is_hidden else 1
        cursor.execute("UPDATE users SET is_hidden = ? WHERE user_id = ?", (new_status, user_id))
        conn.commit()

        text = "✅ Твоя анкета тепер показується." if new_status == 0 else "✅ Твоя анкета прихована."
        await message.answer(text, reply_markup=hide_show_menu(new_status))
    
    conn.close()

@router.message(lambda m: m.text == "🌐 Змінити мову")
async def change_language(message: types.Message):
    await message.answer("🌍 Обери мову:", reply_markup=language_menu())
