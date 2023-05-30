import asyncio
import datetime


import logging.config
import re
import time

from aiogram.client.session import aiohttp
from bs4 import BeautifulSoup
from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from config_data.config import LOGGING_CONFIG, config
from database.db import Transaction, engine, BotSettings
from services.func import get_top100_tokens, format_top_message

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')

err_log = logging.getLogger('errors_logger')


async def add_new_transactions(transactions: list[Transaction]):
    """
    Добавляет новые транзакции в базу
    [['0xf976b8b51421e58bb4217de8b2f82d91790e404168043c4d4a1b5827bd53c7d9'
     'Wrapped Ethe... (WETH)'],]
    """
    # logger.debug(f'add_new_transactions data: {data}\ntoken_adress: {token_adress}')
    start = time.perf_counter()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    count = 0
    for transaction in transactions:
        async with async_session() as session:
            try:
                # Ищем есть ли запись
                result = await session.execute(select(Transaction).filter(
                    Transaction.addet_time > (
                            datetime.datetime.now() - datetime.timedelta(
                                minutes=5)),
                    Transaction.txn_hash == transaction.txn_hash,
                    Transaction.token_name == transaction.token_name
                    ).order_by(Transaction.addet_time.desc()).limit(1))
                result = result.scalars().one_or_none()
                if result:
                    # logger.debug(f'Запись есть в базе: ')
                    continue
                transaction.addet_time = datetime.datetime.now()
                session.add(transaction)
                await session.commit()
                count += 1
                logger.debug(f'добавлено в базу: {transaction}')
            except IntegrityError as err:
                err_log.error(f'Проблема добавления записи {transactions}')
                raise err
    logger.info(f'Добавлено: {count} {time.perf_counter() - start}')


async def get_last_hour_transaction(
        lower_target, time_period=60) -> list[Transaction, int]:
    """
    Возвращает сгруппированный список транзакций за последний час,
     количество которых больше порога.
    :param lower_target: нижний порог количества
    :param time_period: период  обработки, мин
    :return: list[tuple[str, int]]
    [(Transaction, 559),]
    """
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        query = select(
            Transaction, func.count(Transaction.token_adress)).group_by(
            Transaction.token_adress).order_by(
            func.count(Transaction.token_adress).desc()).where(
            (Transaction.addet_time > datetime.datetime.now()
             - datetime.timedelta(minutes=time_period))).having(
            func.count(Transaction.token_adress) > lower_target)
        result = await session.execute(query)
        result = result.all()
        print('res:', result, len(result))
        return result


async def clean(minutes=60):
    """
    Удаляет все Transaction старее minutes назад
    :param minutes: период в минутах
    :return:
    """
    try:
        delta = datetime.timedelta(minutes=minutes)
        async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
            engine, expire_on_commit=False)
        async with async_session() as session:
            await session.execute(delete(Transaction).where(Transaction.addet_time < (
                    datetime.datetime.now() - delta)))
            await session.commit()
        return True
    except Exception as err:
        err_log.error('Ошибка при удалении из базы')
        print(err)


async def read_bot_settings(name: str) -> str:
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings).where(BotSettings.name == name).limit(1)
        result = await session.execute(q)
        readed_setting: BotSettings = result.scalars().one_or_none()
    return readed_setting.value


async def set_botsettings_value(name, value):
    try:
        async_session = async_sessionmaker(engine)
        async with async_session() as session:
            query = select(BotSettings).where(BotSettings.name == name).limit(1)
            result = await session.execute(query)
            setting: BotSettings = result.scalar()
            if setting:
                setting.value = value
            await session.commit()
    except Exception as err:
        err_log.error(f'Ошибка set_botsettings_value. name: {name}, value: {value}')
        raise err


async def find_holders(token_adress: str) -> int:
    """"
    Находит количество Holders по адресу токена
    """
    try:
        headers = {
            'authority': 'etherscan.io',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',  # noqa: E501
            'accept-language': 'ru,en;q=0.9',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "YaBrowser";v="23"',  # noqa: E501
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.4.603 Yowser/2.5 Safari/537.36',   # noqa: E501
        }
        url = f'https://etherscan.io/token/{token_adress}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url,headers=headers) as response:
                html = await response.text()

        soup = BeautifulSoup(html, features='lxml')
        holders_div = soup.find(id='ContentPlaceHolder1_tr_tokenHolders')
        holders_text = holders_div.find('div').text
        holders_value = holders_text.strip().replace(',', '').split(' ')[0]
        return int(holders_value)
    except Exception:
        err_log.error(f'Проблема распознавания Holders {token_adress}')
        pass


async def report():
    try:
        limit_count = int(await read_bot_settings(
            'Etherscanio-parser_lower_limit_count'))
        non_popular_tokens = []
        top100 = await get_top100_tokens()
        stop_token = config.logic.STOP_TOKEN
        period = await read_bot_settings('Etherscanio-parser_report_time')
        period = int(period)
        holders_limit = await read_bot_settings('holders_min_limit')
        holders_limit = int(holders_limit)
        all_transactions = await get_last_hour_transaction(
            limit_count, period)  # [(Transaction, 5944)]
        for transaction, count in all_transactions:
            if transaction.token not in top100 + stop_token:
                holders = await find_holders(transaction.token_adress)
                print(f'Holders {transaction.token}: {holders}')
                if holders > holders_limit:
                    non_popular_tokens.append((transaction, count, holders))
        print('non_popular_tokens:', non_popular_tokens)
        if non_popular_tokens:
            msg = format_top_message(non_popular_tokens)
        else:
            msg = 'Empty'
        return msg
    except Exception:
        err_log.error('report error', exc_info=True)


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
