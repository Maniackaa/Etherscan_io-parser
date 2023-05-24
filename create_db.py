import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from database.db import engine, init_models, BotSettings


async def settings_default():
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings)
        result = await session.execute(q)
        settings = result.all()
        if not settings:
            print('Добавляем настройки по умолчанию')
            settings1 = BotSettings(
                name='Etherscanio-parser_report_time',
                value='60',
                description='Период отправки отчетов, мин.',
            )
            settings2 = BotSettings(
                name='Etherscanio-parser_lower_limit_count',
                value='100',
                description='Нижний порог счетчика токенов для отчета',
            )
            session.add_all([settings1, settings2])
            await session.commit()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_models(engine))
        loop.run_until_complete(settings_default())
    finally:
        loop.close()



