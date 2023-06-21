import asyncio
import logging
import re
import time
import logging.config
import aiohttp
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config_data.config import config, LOGGING_CONFIG
from database.db import Transaction
from database.db_func import read_bot_settings, get_last_hour_transaction

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


def format_top_message(tokens: list[Transaction, int, int]) -> str:
    msg = f'Топ\n'
    for transaction, count, holders in tokens:
        print('---used_transactions:', len(transaction.used_transactions()), transaction.used_transactions())
        if transaction.token_adress in transaction.used_transactions():
            msg += (f'❌{transaction.token} ({count}). Holders: {holders}\n'
                    f'{transaction.token_adress}\n\n')
        else:
            msg += (f'✅{transaction.token} ({count}). Holders: {holders}\n'
                    f'{transaction.token_adress}\n\n')
        transaction.add_trasaction(transaction.token_adress)
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
            address = token_a.get('href', '/token/unknown').split('/token/')[1]
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


def find_transactions(html) -> list[Transaction]:
    soup = BeautifulSoup(html, features='lxml')
    tokens_rows = soup.find_all('tr')[1:]
    transactions: list[Transaction] = []
    for num, row in enumerate(tokens_rows, 1):
        token_name = ''
        token = ''
        columns = row.select('td')
        txn_hash = columns[1].text.strip()
        token_column = columns[10]
        a = token_column.select('a')[0]
        adress = a.get('href').split('/token/')[1].strip()
        spans_token_name = a.select('span')
        for span in spans_token_name:
            span_class = span.get('class')
            if 'text-muted' in span_class:
                token = span.text.strip('()')
            elif 'hash-tag' in span_class:
                token_name = span.text
        new_transaction: Transaction = Transaction(
            txn_hash=txn_hash, token_name=token_name, token=token,
            token_adress=adress
        )
        transactions.append(new_transaction)
    # print(transactions)
    return transactions


async def find_holders(token_adress: str) -> int:
    """"
    Находит количество Holders по адресу токена
    """
    try:
        headers = {
            'authority': 'etherscan.io',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',  # noqa: E501
            'accept-language': 'ru,en;q=0.9',
            'cache-control': 'max-age=0',
            'sec-ch-ua': '"Chromium";v="110", "Not A(Brand";v="24", "YaBrowser";v="23"',  # noqa: E501
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 YaBrowser/23.3.4.603 Yowser/2.5 Safari/537.36',   # noqa: E501
        }
        url = f'https://etherscan.io/token/{token_adress}'

        async with aiohttp.ClientSession() as session:
            async with session.get(url,headers=headers) as response:
                html = await response.text()

        soup = BeautifulSoup(html, features='lxml')
        holders_div = soup.find(id='ContentPlaceHolder1_tr_tokenHolders')
        holders_text = holders_div.find('div').text
        holders_value = holders_text.strip().replace(',', '').split(' ')[0]
        return int(holders_value)
    except Exception:
        err_log.error(f'Проблема распознавания Holders {token_adress}')
        pass


async def report():
    try:
        limit_count = int(await read_bot_settings(
            'Etherscanio-parser_lower_limit_count'))
        non_popular_tokens = []
        top100 = await get_top100_tokens()
        stop_token = config.logic.STOP_TOKEN
        period = await read_bot_settings('Etherscanio-parser_report_time')
        period = int(period)
        print('period', period)
        holders_limit = await read_bot_settings('holders_min_limit')
        holders_limit = int(holders_limit)
        print('holders_limit', holders_limit)
        all_transactions = await get_last_hour_transaction(
            limit_count, period)  # [(Transaction, 5944)]
        print(all_transactions)
        for transaction, count in all_transactions:
            if transaction.token not in top100 + stop_token:
                holders = await find_holders(transaction.token_adress)
                print(f'Holders {transaction.token}: {holders}')
                if holders > holders_limit:

                    non_popular_tokens.append((transaction, count, holders))
        print('non_popular_tokens:', non_popular_tokens)
        if non_popular_tokens:
            msg = format_top_message(non_popular_tokens)
        else:
            msg = 'Empty'

        # for row in non_popular_tokens:
        #     transaction: Transaction = row[0]
        #     transaction.add_trasaction(transaction.token_adress)
        #     print('---', transaction.token_adress)

        return msg
    except Exception:
        err_log.error('report error', exc_info=True)


async def main():
    await report()



if __name__ == '__main__':
    asyncio.run(main())
