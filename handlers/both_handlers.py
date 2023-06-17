import datetime

from aiogram import Dispatcher, types, Router, Bot
from aiogram.filters import Command, CommandStart, Text
from aiogram.types import CallbackQuery, Message
import logging.config

from sqlalchemy import select, String, Integer, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from config_data.config import LOGGING_CONFIG, config
from database.db import Transaction, Base, engine

router: Router = Router()
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')
err_log = logging.getLogger('errors_logger')


engine_uniswap = engine
engine_user = create_async_engine(f"mysql+asyncmy://{config.db.db_user}:{config.db.db_password}@{config.db.db_host}:{config.db.db_port}/userbot_db", echo=False)


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


@router.message(Command(commands=["live"]))
async def process_settings_command(message: Message):
    # последние транзакции uniswap_db.transactions за час
    async with engine_uniswap.begin() as conn:
        transactions_q = await conn.execute(
            select(Transaction.token_adress).group_by(
                'token_adress').having(func.count(Transaction.token_adress) > 1))
        transactions = transactions_q.scalars().all()

    session = async_sessionmaker(engine_user, expire_on_commit=False)
    tokens_res = await session().execute(select(Token).where(
        Token.token.in_(transactions))
    )
    tokens = tokens_res.scalars().all()
    msg = 'Живые токены из uniswap:\n'
    for token in tokens:
        msg += f'{token.token}\n'
    await message.answer(msg[:2500])
    print(len(msg))





