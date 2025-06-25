# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import is_registered

router = Router()

@router.message(F.text == '/start')
async def start_handler(message: Message):
    user_id = message.from_user.id
    if is_registered(user_id):
        builder = InlineKeyboardBuilder()
        builder.button(text="🔍 Переглянути анкети", callback_data="browse_profiles")
        builder.button(text="✏️ Змінити анкету", callback_data="restart")
        builder.button(text="❌ Видалити акаунт", callback_data="delete_profile")
        builder.adjust(1)
        await message.answer(
            "👋 Привіт! Ти вже зареєстрований у боті. Що хочеш зробити?",
            reply_markup=builder.as_markup()
        )
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Запустити", callback_data="launch_bot")
    await message.answer(
        "🤖 *Цей бот допоможе тобі знайти друзів або пару!*\n\n"
        "👋 Швидке знайомство\n"
        "💬 Анонімний чат\n"
        "📸 Надсилання фото\n"
        "🔒 Безпечне спілкування",
        reply_markup=builder.as_markup(), parse_mode="Markdown")

@router.callback_query(F.data == "launch_bot")
async def choose_language(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    languages = ["Українська 🇺🇦", "English 🇬🇧", "Deutsch 🇩🇪", "Español 🇪🇸",
                 "Français 🇫🇷", "Italiano 🇮🇹", "Polski 🇵🇱", "Türkçe 🇹🇷"]
    for lang in languages:
        builder.button(text=lang, callback_data=f"lang_{lang}")
    builder.adjust(1)
    await callback.message.edit_text("🌍 Обери мову:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("lang_"))
async def language_selected(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="👉 ДАВАЙ ПОЧНЕМО", callback_data="lets_start")
    await callback.message.edit_text(
        "Вже мільйони людей знайомляться в Дайвінчику 😍\n\n"
        "Я допоможу знайти тобі пару або просто друзів 👫",
        reply_markup=builder.as_markup())

@router.callback_query(F.data == "lets_start")
async def show_rules(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ ОКЕЙ", callback_data="agree")
    await callback.message.edit_text(
        "❗️ Пам'ятайте, що в Інтернеті люди можуть виступати в ролі інших осіб.\n\n"
        "Продовжуючи, ви приймаєте угоду користувача та політику конфіденційності.",
        reply_markup=builder.as_markup())

@router.callback_query(F.data == "delete_profile")
async def delete_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    from database.db import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM likes WHERE liker_id = ? OR liked_id = ?", (user_id, user_id))
    conn.commit()
    conn.close()

    await callback.message.answer("❌ Твій профіль видалено. Щоб створити новий — натисни /start")
    await callback.message.delete()
