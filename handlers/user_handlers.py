import asyncio
from aiogram import Dispatcher, types, Router, Bot
from aiogram.filters import Command, CommandStart, Text
from aiogram.types import CallbackQuery, Message, URLInputFile, KeyboardButton, \
    ReplyKeyboardMarkup
import logging.config
from aiogram.fsm.context import FSMContext


from config_data.config import LOGGING_CONFIG
from database.db_func import set_botsettings_value, read_bot_settings, \
    read_all_bot_settings
from services.func import report

router: Router = Router()
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')
err_log = logging.getLogger('errors_logger')


kb = [
    [KeyboardButton(text="/report")],
    [KeyboardButton(text="/live")],
    ]

start_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=kb,
                                                    resize_keyboard=True)


@router.message(Command(commands=["start"]))
async def process_start_command(message: Message, state: FSMContext):
    print('start')
    await state.clear()
    text = (f'Привет!\n'
            f'Команды:\n'
            f'/report -  отчет.\n'
            f'/live - показать живые токены из uniswap.\n'
            f'/settings: показать текущие настройки\n\n'
            f'Изменить настройки:\n'
            f'set:period:60 - изменить период обработки, мин.\n'
            f'set:limit:100 - изменить порог счетчика.\n'
            f'set:holders:3000 - изменить порог холдеров для отчета.\n'
            f'set:HONEYPOT_DELAY:720 - Задержка перед проверкой  на is_honeypot, в минутах\n'
            f'set:live_period:30 - Период за сколько мин. искать  транзакции для сравнения с базой uniswap\n'
            )
    await message.answer(text, reply_markup=start_kb)


@router.message(Command(commands=["report"]))
async def process_start_command(message: Message):
    print('report')
    await message.answer('Запрос обрабатывается. Ждите!')
    text = f'Report\n'
    text += await report() or 'empty'
    print(text)
    for x in range(0, len(text), 2500):
        mess = text[x: x + 2500]
        await asyncio.sleep(0.1)
        await message.answer(mess)


@router.message(Text(startswith='set:'))
async def process_start_command(message: Message):
    # set:limit:100
    try:
        command = message.text.split(':')
        name = command[1]
        value = command[2]
        if name == 'limit' and value:
            settings_name = 'Etherscanio-parser_lower_limit_count'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        elif name == 'period' and value:
            settings_name = 'Etherscanio-parser_report_time'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        elif name == 'holders' and value:
            settings_name = 'holders_min_limit'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        elif name == 'HONEYPOT_DELAY' and value:
            settings_name = 'HONEYPOT_DELAY'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        elif name == 'live_period' and value:
            settings_name = 'live_period'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        else:
            await message.answer(f'Неизвестная команда')
    except IndexError:
        await message.answer(f'Неверный формат команды')


# @router.message(Command(commands=["settings"]))
# async def process_settings_command(message: Message):
#     print('setings')
#     period = await read_bot_settings('Etherscanio-parser_report_time')
#     limit = await read_bot_settings('Etherscanio-parser_lower_limit_count')
#     text = (f'Текущие настройки:\n\n'
#             f'Период отправки отчетов, мин: {period}\n'
#             f'Нижний порог счетчика токенов для отчета: {limit}')
#     await message.answer(text[:2500])


@router.message(Command(commands=["settings"]))
async def process_settings_command(message: Message):

    print('setings')
    settings = await read_all_bot_settings()
    text = f'Текущие настройки:\n\n'
    for setting in settings:
        text += f'{setting.description}:\n{setting.name}: {setting.value}\n\n'
        print(settings, setting.name)
    await message.answer(text)