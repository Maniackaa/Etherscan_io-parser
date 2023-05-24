from aiogram import Dispatcher, types, Router, Bot
from aiogram.filters import Command, CommandStart, Text
from aiogram.types import CallbackQuery, Message, URLInputFile

from aiogram.fsm.context import FSMContext

from database.db_func import set_botsettings_value, get_last_hour_transaction, \
    report

router: Router = Router()


@router.message(Command(commands=["start"]))
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    text = (f'Привет!\n'
            f'Настройки:\n'
            f'set:limit:50 - изменить порог счетчика.\n'
            f'set:period:50 - изменить период отчета, мин.\n'
            )
    await message.answer(text)


@router.message(Command(commands=["report"]))
async def process_start_command(message: Message):
    text = await report()
    await message.answer(text)


@router.message(Text(startswith='set:'))
async def process_start_command(message: Message):
    # set:limit:100
    try:
        command = message.text.split(':')
        name = command[1]
        value = command[2]
        if name == 'limit':
            settings_name = 'Etherscanio-parser_lower_limit_count'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        elif name == 'period':
            settings_name = 'Etherscanio-parser_report_time'
            await set_botsettings_value(settings_name, value)
            await message.answer(f'{name}, {value}')
        else:
            await message.answer(f'Неизвестная команда')
    except IndexError:
        await message.answer(f'Неверный формат команды')
