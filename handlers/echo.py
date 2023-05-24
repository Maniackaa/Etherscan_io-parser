from datetime import datetime

from aiogram import Router
from aiogram.types import Message


router: Router = Router()


# Последний эхо-фильтр
@router.message()
async def send_echo(message: Message):
    print(message)
    await message.reply(text=message.text)


