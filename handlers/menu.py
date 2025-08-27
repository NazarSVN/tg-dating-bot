from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from states import Form
from .profile import send_next_profile
from database.models import record_like, check_mutual_like

router = Router()

# Реплай меню
end_of_profiles_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📑 Дивитися анкети")],
        [KeyboardButton(text="✏️ Заповнити анкету наново")],
        [KeyboardButton(text="👀 Хто мене лайкнув")],
        [KeyboardButton(text="❤️ Лайк"), KeyboardButton(text="➡️ Пропустити")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


# /start
@router.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer("Вибери дію:", reply_markup=end_of_profiles_menu)


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


# Хто мене лайкнув
@router.message(lambda m: m.text == "👀 Хто мене лайкнув")
async def who_liked(message: types.Message):
    from database.models import get_connection
    import json, os
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
        caption = f"❤️ {name}"
        if photos and os.path.exists(photos[0]):
            from aiogram.types import FSInputFile
            photo_input = FSInputFile(photos[0])
            await message.answer_photo(photo=photo_input, caption=caption)
        else:
            await message.answer(caption)


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

    if check_mutual_like(liker_id, liked_user_id):
        await message.answer(f"🎉 Ура! У тебе взаємний лайк з користувачем {liked_user_id}!")
    else:
        await message.answer("Лайк поставлено ✅")

    # Наступна анкета
    next_profile_id = await send_next_profile(message, liker_id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)


# Пропустити профіль
@router.message(lambda m: m.text == "➡️ Пропустити")
async def skip_profile(message: types.Message, state: FSMContext):
    next_profile_id = await send_next_profile(message, message.from_user.id)
    if next_profile_id:
        await state.update_data(current_profile_id=next_profile_id)
