import asyncio
import datetime
import sys

from sqlalchemy import create_engine, ForeignKey, Date, String, \
    UniqueConstraint, Float, DateTime, Integer
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.ext.asyncio import create_async_engine

from config_data.config import config

engine = create_async_engine(f"mysql+asyncmy://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/{config.db.database}", echo=False)


class Base(DeclarativeBase):
    pass


class Transaction(Base):
    __tablename__ = 'transactions'
    used_transacrions = set()
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    txn_hash: Mapped[str] = mapped_column(String(100))
    token_name: Mapped[str] = mapped_column(String(50))
    token: Mapped[str] = mapped_column(String(20))
    token_adress: Mapped[str] = mapped_column(String(100))
    addet_time: Mapped[str] = mapped_column(DateTime(), default=str(
        datetime.datetime.now()))

    @classmethod
    def used_transactions(cls):
        return cls.used_transacrions

    @classmethod
    def add_trasaction(cls, adress):
        cls.used_transacrions.add(adress)

    @classmethod
    def clear_transaction(cls):
        cls.used_transacrions = set()

    def __str__(self):
        return f'{self.id} {self.token_name} {self.token} {self.token_adress} {self.addet_time}'

    def __repr__(self):
        return f'{self.id} token_name: {self.token_name}, token: {self.token}, token_adress: {self.token_adress}, {self.addet_time}'

#
# class Report(Base):
#     __tablename__ = 'reports'
#     id: Mapped[int] = mapped_column(primary_key=True,
#                                     autoincrement=True,
#                                     comment='Первичный ключ')
#     addet_time: Mapped[str] = mapped_column(DateTime(), default=str(
#         datetime.datetime.now()))
#     text: Mapped[str] = mapped_column(String(5000))


class BotSettings(Base):
    __tablename__ = 'bot_settings'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    name: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(50), nullable=True, default='')
    description: Mapped[str] = mapped_column(String(255),
                                             nullable=True,
                                             default='')

    def __repr__(self):
        return f'{self.id}. {self.name}: {self.value}'

async def init_models(engine):
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == '__main__':
    if sys.version_info[:2] == (3, 7):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_models(engine))
        loop.run_until_complete(asyncio.sleep(2.0))
    finally:
        loop.close()

