import asyncio
import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

from database.db import engine


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
    addet_time: Mapped[str] = mapped_column(DateTime(), default=str(
        datetime.datetime.now()))

    def __repr__(self):
        return f'{self.id} {self.token_name} {self.addet_time}'


async def init_models():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_models())
        loop.run_until_complete(asyncio.sleep(2.0))
    finally:
        loop.close()
