import asyncio
import datetime
import sys

from sqlalchemy import create_engine, ForeignKey, Date, String, \
    UniqueConstraint, Float, DateTime
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
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    txn_hash: Mapped[str] = mapped_column(String(100))
    token_name: Mapped[str] = mapped_column(String(50))
    token: Mapped[str] = mapped_column(String(20))
    token_adress: Mapped[str] = mapped_column(String(100))
    addet_time: Mapped[str] = mapped_column(DateTime(), default=str(
        datetime.datetime.now()))

    def __repr__(self):
        return f'{self.id} {self.token_name} {self.addet_time}'

# class Token(Base):
#     __tablename__ = 'token_adress'
#     id: Mapped[int] = mapped_column(primary_key=True,
#                                     autoincrement=True,
#                                     comment='Первичный ключ')
#     token_name: Mapped[str] = mapped_column(String(50))
#     token_adress: Mapped[str] = mapped_column(String(100))
#
#     def __repr__(self):
#         return f'{self.id}. {self.token_name}: {self.token_adress}'


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

