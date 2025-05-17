import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import TOKEN
from app.database.models import async_main
from app.handlers import router
from app.admin import admin


async def main():
    #создание базы данных
    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Подключаем обычные и админские комманды бота
    dp.include_routers(admin, router)

    # Запускаем слушатель событий
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')
