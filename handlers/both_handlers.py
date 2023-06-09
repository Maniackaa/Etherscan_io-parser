import datetime

from aiogram import Dispatcher, types, Router, Bot
from aiogram.filters import Command, CommandStart, Text
from aiogram.types import CallbackQuery, Message
import logging.config

from sqlalchemy import select, String, Integer, func, DateTime, update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from config_data.config import LOGGING_CONFIG, config
from database.db import Transaction, Base, engine
from database.db_func import read_bot_settings

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
    last_call: Mapped[str] = mapped_column(DateTime())

    def __repr__(self):
        return f'{self.id}. {self.token}'


async def change_token_last_call(token_adress):
    """
     Проверяет время когда токен попадал в /live.
     Если уже попадал, то возвращает False
     Если null, то ставит текущее время.
    :param token:
    :return:
    """
    try:
        logger.debug(f'Смотрим last_call токена {token_adress} в базе userbot_db')
        async_session = async_sessionmaker(engine_user)
        async with async_session(expire_on_commit=False) as session:
            query = select(Token).where(Token.token == token_adress)
            token_q = await session.execute(query)
            token = token_q.scalar()
            if token.last_call is None:
                token.last_call = datetime.datetime.utcnow()
                session.add(token)
                await session.commit()
                logger.debug(f'Сохранили last_call: {token}. ТОкен помечен: {token.last_call}')
                return True
            else:
                logger.debug(f'Ужк помечен')
                return False

    except Exception as err:
        raise err


async def clear_call():
    try:
        logger.debug(f'Очищаем /last_call')
        async_session = async_sessionmaker(engine_user)
        async with async_session(expire_on_commit=False) as session:
            query = update(Token).where(Token.last_call.is_not(None)).values(last_call=None)
            token_q = await session.execute(query)
            print(token_q)
            await session.commit()
    except Exception:
        logger.error('Ошибка обнуления last_cal')


@router.message(Command(commands=["cl"]))
async def process_settings_command(message: Message):
    # Все годные токены UserbotEtherscan которые старые
    await clear_call()
    await message.answer('Обнулены')


@router.message(Command(commands=["live"]))
async def process_settings_command(message: Message):
    # Все годные токены UserbotEtherscan которые старые
    session = async_sessionmaker(engine_user, expire_on_commit=False)()
    tokens_res = await session.execute(select(Token.token).where(Token.message_sended == '1'))
    tokens = tokens_res.scalars().all()
    await session.close()

    # последние транзакции uniswap_db.transactions за час + которые выше
    live_period = await read_bot_settings('live_period')
    live_period = int(live_period)
    async with engine_uniswap.begin() as conn:
        transactions_q = await conn.execute(
            select(Transaction.token, Transaction.token_adress).where(Transaction.token_adress.in_(tokens)).where(
             (Transaction.addet_time > datetime.datetime.now()
              - datetime.timedelta(minutes=live_period))).group_by('token_adress'))
        transactions = transactions_q.all()

    msg = 'Живые токены из uniswap:\n'
    for transaction in transactions:
        token = transaction[1]
        first = await change_token_last_call(token)
        msg += f'✅({transaction[0]}) {transaction[1]}\n' if first else f'❌({transaction[0]}) {transaction[1]}\n'
    #
    if len(msg) > 2500:
        for x in range(0, len(msg), 4096):
            await message.answer(msg[x:x + 4096])
    else:
        await message.answer(msg)






