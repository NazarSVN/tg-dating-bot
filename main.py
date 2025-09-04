import asyncio
from aiogram import Bot, Dispatcher
from config import TELEGRAM_TOKEN
from handlers import start, registration, photo, menu, profile
from database.models import init_db

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(registration.router)
dp.include_router(photo.router)
dp.include_router(menu.router)
dp.include_router(profile.router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    init_db()
    asyncio.run(main())
