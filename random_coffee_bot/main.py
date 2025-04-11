import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import Config, load_config
from handlers.admin_handlers import admin_router
from handlers.users_handlers import user_router


logger = logging.getLogger(__name__)


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    logger.info('Старт бота')

    # Из переменной config можно получить переменные окружения в текущем файле.
    config: Config = load_config()

    bot = Bot(
        token=config.tg_bot.token
    )
    dp = Dispatcher()

    dp.include_router(admin_router)
    dp.include_router(user_router)

    await dp.start_polling(bot)

asyncio.run(main())
