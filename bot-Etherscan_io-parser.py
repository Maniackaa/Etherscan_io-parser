import asyncio

import logging.config
from aiogram import Bot, Dispatcher

from config_data.config import LOGGING_CONFIG, config
from handlers import user_handlers, echo, both_handlers

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')
err_log = logging.getLogger('errors_logger')


async def main():
    logger.info('Starting bot')
    bot: Bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher()

    # Регистриуем
    dp.include_router(user_handlers.router)
    dp.include_router(both_handlers.router)
    dp.include_router(echo.router)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.send_message(config.tg_bot.admin_ids[0],
                           f'Бот запущен.')
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Bot stopped!')
