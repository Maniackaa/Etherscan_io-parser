import asyncio
import datetime
import sys


from sqlalchemy import create_engine, ForeignKey, Date, String, \
    UniqueConstraint, Float, DateTime, func, select, Integer
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.ext.asyncio import create_async_engine

from config_data.config import config
from database.db import Transaction, Base

engine = create_async_engine(f"mysql+asyncmy://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/uniswap_db", echo=False)
engine_userbot = create_async_engine(f"mysql+asyncmy://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/userbot_db", echo=False)

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession


class Token(Base):
    __tablename__ = 'tokens'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    date: Mapped[str] = mapped_column(String(30), default=str(datetime.datetime.utcnow()))
    token: Mapped[str] = mapped_column(String(255))
    token_url: Mapped[str] = mapped_column(String(500))
    weth: Mapped[int] = mapped_column(String(255))
    score: Mapped[str] = mapped_column(String(500), nullable=True, default='')
    is_honeypot: Mapped[str] = mapped_column(String(255), nullable=True, default='')
    holders: Mapped[int] = mapped_column(Integer(), nullable=True)
    message_sended: Mapped[str] = mapped_column(String(30), default='')

    def __repr__(self):
        return f'{self.id}. {self.token}'


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
        async_session = async_sessionmaker(engine_userbot, expire_on_commit=False)
        async with async_session() as session:
            query = select(Token)
            res2 = await session.execute(query)
            print('res2', res2.scalars().all())

        return result




async def main():
    x = await get_last_hour_transaction(1, 2)
    print(x)


if __name__ == '__main__':
    asyncio.run(main())
