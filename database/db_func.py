import asyncio
import datetime
import logging.config
import re
import time

from sqlalchemy import select, delete, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from config_data.config import LOGGING_CONFIG
from database.db import Transaction, engine, BotSettings

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')
err_log = logging.getLogger('errors_logger')


async def add_new_transactions(data: list, token_adress: dict):
    """
    Добавляет новые транзакции в базу
    [['0xf976b8b51421e58bb4217de8b2f82d91790e404168043c4d4a1b5827bd53c7d9'
     'Wrapped Ethe... (WETH)'],]
    """
    logger.debug(f'add_new_transactions data: {data}\ntoken_adress: {token_adress}')
    start = time.perf_counter()
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    count = 0
    for row in data:
        tnx_hash = row[0]
        token_name = row[1]
        transaction = Transaction()
        async with async_session() as session:
            try:
                # Ищем есть ли запись
                result = await session.execute(select(Transaction).filter(
                    Transaction.addet_time > (
                            datetime.datetime.now() - datetime.timedelta(
                                minutes=5)),
                    Transaction.txn_hash == tnx_hash,
                    Transaction.token_name == token_name
                    ).order_by(Transaction.addet_time.desc()).limit(1))
                result = result.scalars().one_or_none()
                if result:
                    logger.debug(f'Запись есть в базе: ')
                    continue
                transaction.txn_hash = tnx_hash
                transaction.token_name = token_name
                token = re.search('\((.+)\)', token_name)
                if token:
                    token = token.group(1)
                transaction.token = token or 'unknown'
                transaction.addet_time = datetime.datetime.now()
                transaction.token_adress = token_adress.get(
                    transaction.token, 'unknown')
                session.add(transaction)
                await session.commit()
                count += 1
                logger.debug(f'Запись ДОБАВЛЕНА в базу')
            except IntegrityError as err:
                err_log.error(f'Проблема добавления записи {row}')
                raise err
    logger.info(f'Добавлено: {count} {time.perf_counter() - start}')


async def get_last_hour_transaction(lower_target) -> list[(str, int)]:
    """
    Возвращает сгруппированный список транзакций за последний час,
     количество которых больше порога.
    :param lower_target: нижний порог количества
    :return: list[tuple[str, int]]
    [('WETH', 559, '0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2'),]
    """
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        query = select(
            Transaction.token, func.count(
                Transaction.token), Transaction.token_adress).group_by(
            Transaction.token).order_by(
            func.count(Transaction.token).desc()).where(
            (Transaction.addet_time > datetime.datetime.now()
             - datetime.timedelta(minutes=60))).having(
            func.count(Transaction.token) > lower_target)
        result = await session.execute(query)
        result = result.all()
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


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
