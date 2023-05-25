import logging
import re
import time
import logging.config
import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config_data.config import config, LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
err_log = logging.getLogger('errors_logger')
logger = logging.getLogger('my_logger')


def get_df_from_html(html):
    df = pd.read_html(html)[0]
    df = df.iloc[:, [1, 8]]
    return df


async def get_top100_tokens():
    """
    Читает список топ100 токенов и доавляет их в лист.
    :return: list[str]
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        'Referer': 'https://etherscan.io/tokens',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }
    params = {'p': '1'}
    async with aiohttp.ClientSession() as session:
        async with session.get('https://etherscan.io/tokens',
                               params=params,
                               headers=headers) as response1:
            html1 = await response1.text()
            df1 = pd.read_html(html1)[0]
        async with session.get('https://etherscan.io/tokens',
                               params=params,
                               headers=headers) as response2:
            html2 = await response2.text()
            df2 = pd.read_html(html2)[0]
    df = pd.concat([df1, df2]).reset_index()
    top100_tokens_df = df.iloc[:, [2]]
    top100 = []
    for row in top100_tokens_df.values:
        line = row[0]
        res = re.search('\((.+)\)', line)
        if res:
            res = res.group(1)
        top100.append(res or 'unknown')
    return top100


def format_top_message(tokens: list[tuple]) -> str:
    msg = f'Топ\n'
    for token in tokens:
        msg += f'{token[0]} ({token[1]})\n{token[2]}\n\n'
    return msg


def send_message_tg(message: str, chat_id: str):
    """Отправка сообщения через чат-бот телеграмма"""
    print(f'Отправка сообщения {chat_id} {message}')
    message = message[:2500]
    bot_token = config.tg_bot.token
    url = (f'https://api.telegram.org/'
           f'bot{bot_token}/'
           f'sendMessage?'
           f'chat_id={chat_id}&'
           f'text={message}')
    requests.get(url)


def get_adress_from_html(html):
    soup = BeautifulSoup(html, features='lxml')
    tokens_a = soup.find_all('a',
                             class_='d-flex align-items-center gap-1 link-dark')
    token_adress = {}
    for token_a in tokens_a:
        try:
            address = token_a.get('href','/token/unknown').split('/token/')[1]
            span = token_a.select('div > span ')
            if len(span) == 2:
                token_name = span[1].text.strip('()')
            else:
                token_name = span[0].text
            token_adress[token_name] = address
        except IndexError:
            err_log.debug(f'Ошибка на token_a: {token_a}', exc_info=True)
            continue
        except Exception as err:
            err_log.debug(f'{token_a or token_adress}', exc_info=True)
            raise err
    return token_adress
