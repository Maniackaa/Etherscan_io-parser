import time

import requests
from bs4 import BeautifulSoup

from database.db import Transaction

parsing_transactions_headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/113.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Referer': 'https://etherscan.io/tokentxns?ps=100&p=2',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',

}
params = {
    'ps': '100',
    'p': '1',
}

time_point = time.perf_counter()
response = requests.get('https://etherscan.io/tokentxns',
                        params=params,
                        headers=parsing_transactions_headers)

html = response.text


soup = BeautifulSoup(html, features='lxml')
tokens_rows = soup.find_all('tr')[1:]
transactions: list[Transaction] = []
print(len(tokens_rows))
for num, row in enumerate(tokens_rows, 1):
    # print('-------------')
    # print(row, type(row))
    # print('-------------')
    # print()



    columns = row.select('td')
    txn_hash = columns[1].text.strip()

    print('age', columns[4].text)


    token = columns[10]
    a = token.select('a')[0]
    adress = a.get('href').split('/token/')[1].strip()

    spans_token_name = a.select('span')
    for span in spans_token_name:
        # print(span)
        span_class = span.get('class')
        if 'text-muted' in span_class:
            token = span.text.strip('()')
        elif 'hash-tag' in span_class:
            token_name = span.text


    print(num, 'token_name:', token_name)
    print('token:', token)
    print('txn_hash:', txn_hash)
    print('adress:', adress)
    print()
    new_transaction: Transaction = Transaction(
        txn_hash=txn_hash, token_name=token_name, token=token, token_adress=adress
    )
    transactions.append(new_transaction)

print(*transactions, sep='\n')