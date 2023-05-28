import time

import requests
from bs4 import BeautifulSoup

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
tokens_a = soup.find_all('a',
                         class_='d-flex align-items-center gap-1 link-dark')
token_adress = {}
token_adress_set = []
for token_a in tokens_a:
    address = token_a.get('href', '/token/unknown').split('/token/')[1]
    span = token_a.select('div > span ')
    if len(span) == 2:
        token_name = span[1].text.strip('()')
    else:
        token_name = span[0].text
    print(token_name, address)
    token_adress[token_name] = address
    token_adress_set.append((token_name, address))

token_adress_set = set(token_adress_set)


for t in sorted(token_adress_set):
    print(t)

print(len(token_adress), token_adress)
print(len(token_adress_set), token_adress_set)