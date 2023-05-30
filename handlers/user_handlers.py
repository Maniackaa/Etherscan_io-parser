from aiogram import Dispatcher, types, Router, Bot
from aiogram.filters import Command, CommandStart, Text
from aiogram.types import CallbackQuery, Message, URLInputFile, KeyboardButton, \
    ReplyKeyboardMarkup
import logging.config
from aiogram.fsm.context import FSMContext

from config_data.config import LOGGING_CONFIG
from database.db_func import set_botsettings_value, get_last_hour_transaction, \
    report, read_bot_settings

router: Router = Router()
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger('my_logger')
err_log = logging.getLogger('errors_logger')


kb = [
    [KeyboardButton(text="/report")],
    ]

start_kb: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=kb,
                                                    resize_keyboard=True)

@router.message(Command(commands=["start"]))
async def process_start_command(message: Message, state: FSMContext):
    print('start')
    await state.clear()
    text = (f'Привет!\n'
            f'Команды:\n'
            f'/report: отчет.\n'
            f'/settings: показать текущие настройки\n\n'
            f'Изменить настройки:\n'
            f'set:period:50 - изменить период обработки, мин.\n'
            f'set:limit:50 - изменить порог счетчика.\n'
            )
    await message.answer(text, reply_markup=start_kb)


@router.message(Command(commands=["report"]))
async def process_start_command(message: Message):
    print('report')
    text = f'Report\n'
    text += await report() or 'empty'
    print(text)
    await message.answer(text[:2500])


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
        else:
            await message.answer(f'Неизвестная команда')
    except IndexError:
        await message.answer(f'Неверный формат команды')


@router.message(Command(commands=["settings"]))
async def process_settings_command(message: Message):
    print('setings')
    period = await read_bot_settings('Etherscanio-parser_report_time')
    limit = await read_bot_settings('Etherscanio-parser_lower_limit_count')
    text = (f'Текущие настройки:\n\n'
            f'Период отправки отчетов, мин: {period}\n'
            f'Нижний порог счетчика токенов для отчета: {limit}')
    await message.answer(text[:2500])
