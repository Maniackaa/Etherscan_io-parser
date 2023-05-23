import asyncio
import logging.config
import sys
import time

import requests

from config_data.config import LOGGING_CONFIG, config
from database.db import init_models, engine
from database.db_func import add_new_transactions, clean, \
    get_last_hour_transaction
from services.func import get_df_from_html, get_top100_tokens, \
    format_top_message, send_message_tg

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')
err_log = logging.getLogger('errors_logger')


async def main():
    """
    Циклический парсинг новых транзакций и добавление в базу.
    :return: None
    """
    asyncio.create_task(every_hour_report())
    asyncio.create_task(db_cleaner())


    parsing_transactions_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://etherscan.io/tokentxns?ps=100&p=2',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',

    }
    params = {
        'ps': '100',
        'p': '1',
    }
    while True:
        try:
            time_point = time.perf_counter()
            response = requests.get('https://etherscan.io/tokentxns',
                                    params=params,
                                    headers=parsing_transactions_headers)
            if response.ok:
                time_point1 = time.perf_counter()
                logger.debug(f'Время запроса: {time_point1 - time_point}')
                # Получение транзакций
                transactions_df = get_df_from_html(response.text)
                # Добавление в базу
                await add_new_transactions(transactions_df.values)
                time_point2 = time.perf_counter()
                logger.debug(f'Время обработки: {time_point2 - time_point1}')
                logger.debug(f'Общее время: {time_point2 - time_point}')
            else:
                logger.warning(f'Плохой ответ при парсинге транзакций')
        except Exception:
            err_log.error(f'Ошибка при парсисинге транзакций', exc_info=True)


async def db_cleaner():
    """
    Периодическая очитка базы (периоод в минутах).
    :return:
    """
    while True:
        logger.info('Очистка базы')
        clean_result = await clean(1)
        if clean_result:
            logger.info('База почищена')
        else:
            err_log.error('База не очищена', exc_info=True)
            await asyncio.sleep(5)
            continue
        await asyncio.sleep(60 * 5)


async def every_hour_report():
    while True:
        try:
            non_popular_tokens = []
            top100 = await get_top100_tokens()
            all_transactions = await get_last_hour_transaction(100)  # [('WETH', 4027),]
            for token in all_transactions:
                if token[0] not in top100:
                    non_popular_tokens.append(token)
            msg = format_top_message(non_popular_tokens)
            send_message_tg(msg, config.tg_bot.admin_ids[0])
            await asyncio.sleep(60 * 60)
        except Exception as err:
            err_log.error('every_hour_report error', exc_info=True)
            await asyncio.sleep(5)


if __name__ == '__main__':
    if sys.version_info[:2] == (3, 7):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_models(engine))
    loop.close()
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info('Скрипт остановлен принудительно')

