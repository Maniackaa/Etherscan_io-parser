import asyncio
import datetime


import logging.config
import time

from sqlalchemy import select, delete, func, String, Integer, DateTime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, \
    create_async_engine
from sqlalchemy.orm import mapped_column, Mapped

from config_data.config import LOGGING_CONFIG, config
from database.db import Transaction, engine, BotSettings, Base

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')

err_log = logging.getLogger('errors_logger')

engine_user = create_async_engine(f"mysql+asyncmy://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/userbot_db", echo=False)


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


async def read_all_bot_settings():
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings)
        result = await session.execute(q)
        readed_setting: BotSettings = result.scalars().all()
    print(readed_setting)
    return readed_setting


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
    # await get_last_hour_transaction(1, 2)
    pass

if __name__ == '__main__':
    asyncio.run(main())

