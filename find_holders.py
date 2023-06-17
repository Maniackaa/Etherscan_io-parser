import asyncio
import re
import time
import aiohttp
import asyncio
import requests
from bs4 import BeautifulSoup


async def find_holders(token_adress: str, delay: float = 0.5) -> int:
    """"
    Находит количество Holders по адресу токена
    """
    start = time.perf_counter()
    try:
        await asyncio.sleep(delay)
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
            async with session.get(url, headers=headers) as response:
                html = await response.text()

        soup = BeautifulSoup(html, features='lxml')
        holders_div = soup.find(id='ContentPlaceHolder1_tr_tokenHolders')
        holders_text = holders_div.find('div').text.strip().replace(',', '').split(' ')
        print(holders_text)
        print(time.perf_counter() - start)
        return int(holders_text[0])
    except Exception:
        pass


# x = asyncio.run(find_holders('0x967da4048cd07ab37855c090aaf366e4ce1b9f48'))
# print(x)
async def main():
    task1 = asyncio.create_task(find_holders('0x967da4048cd07ab37855c090aaf366e4ce1b9f48'))
    # task2 = asyncio.create_task(find_holders('0xaf9f549774ecedbd0966c52f250acc548d3f36e5'))
    tasks = [task1]
    # group = asyncio.gather(find_holders('0x967da4048cd07ab37855c090aaf366e4ce1b9f48'), find_holders('0xaf9f549774ecedbd0966c52f250acc548d3f36e5'))
    result = await asyncio.gather(*tasks)
    # await group
    # print(group)
    # print(group.result())
    for res in result:
        print('res:', res)

asyncio.run(main())
