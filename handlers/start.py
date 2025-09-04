from aiogram import Router, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from database.models import is_registered
from states import Form as RegistrationState
from aiogram.fsm.context import FSMContext
from states import Form
from aiogram.types import ReplyKeyboardRemove
from handlers.registration import start_registration

router = Router()

# --- Меню ReplyKeyboard ---
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Переглянути анкети")],
            [KeyboardButton(text="✏️ Змінити анкету")],
            [KeyboardButton(text="❌ Видалити акаунт")]
        ],
        resize_keyboard=True
    )

def language_menu():
    langs = ["Українська 🇺🇦", "English 🇬🇧", "Deutsch 🇩🇪", "Español 🇪🇸",
             "Français 🇫🇷", "Italiano 🇮🇹", "Polski 🇵🇱", "Türkçe 🇹🇷"]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=lang)] for lang in langs],
        resize_keyboard=True
    )

def start_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👉 ДАВАЙ ПОЧНЕМО")]],
        resize_keyboard=True
    )

def rules_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ ОКЕЙ")]],
        resize_keyboard=True
    )

def launch_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🚀 Запустити")]],
        resize_keyboard=True
    )


@router.message(F.text == '/start')
async def start_handler(message: Message):
    user_id = message.from_user.id
    if is_registered(user_id):
        await message.answer(
            "👋 Привіт! Ти вже зареєстрований у боті. Що хочеш зробити?",
            reply_markup=main_menu()
        )
        return

    await message.answer(
        "🤖 Цей бот допоможе знайти друзів або пару!\n\n"
        "👋 Швидке знайомство\n"
        "💬 Анонімний чат\n"
        "📸 Надсилання фото\n"
        "🔒 Безпечне спілкування",
        reply_markup=launch_menu()
    )

@router.message(F.text == "🚀 Запустити")
async def choose_language(message: Message):
    await message.answer("🌍 Обери мову:", reply_markup=language_menu())

@router.message(lambda m: m.text in ["Українська 🇺🇦", "English 🇬🇧", "Deutsch 🇩🇪", "Español 🇪🇸",
                                     "Français 🇫🇷", "Italiano 🇮🇹", "Polski 🇵🇱", "Türkçe 🇹🇷"])
async def language_selected(message: Message):
    await message.answer(
        "Вже мільйони людей знайомляться в телеграмі 😍\n\n"
        "Я допоможу знайти тобі пару або просто друзів 👫",
        reply_markup=start_menu()
    )

@router.message(F.text == "👉 ДАВАЙ ПОЧНЕМО")
async def show_rules(message: Message):
    await message.answer(
        "❗️ Пам'ятайте, що в Інтернеті люди можуть виступати в ролі інших осіб.\n\n"
        "Продовжуючи, ви приймаєте угоду користувача та політику конфіденційності.",
        reply_markup=rules_menu()
    )

# --- Обробник кнопки "✅ ОКЕЙ" ---
@router.message(F.text == "✅ ОКЕЙ")
async def agree_rules(message: Message, state: FSMContext):
    await start_registration(message, state)


async def start_registration(message: Message, state: FSMContext):
    await state.clear()  # очищаємо попередні дані
    await state.set_state(Form.age)  # перший стан
    await message.answer(
        "Привіт! Почнемо реєстрацію.\nСкільки тобі років? (від 14 до 60)",
        reply_markup=ReplyKeyboardRemove() 
    )

@router.message(F.text == "❌ Видалити акаунт")
async def delete_profile(message: Message):
    user_id = message.from_user.id
    from database.db import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM likes WHERE liker_id = ? OR liked_id = ?", (user_id, user_id))
    conn.commit()
    conn.close()

    await message.answer("❌ Твій профіль видалено. Щоб створити новий — натисни /start")

@router.message(F.text == "✏️ Змінити анкету")
async def restart_profile(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(RegistrationState.age)
    await message.answer("🔁 Давай почнемо заново! Скільки тобі років?")
