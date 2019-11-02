import aiohttp
import asyncio
import pymorphy2
from bs4 import BeautifulSoup

import os
import sys
from text_tools import split_by_words
from text_tools import calculate_jaundice_rate
from adapters import SANITIZERS


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def get_morth_raw(_html):
    sanitize = SANITIZERS["inosmi_ru"]
    clean_text = sanitize(_html)
    return clean_text


async def main():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, 'https://inosmi.ru/economic/20191101/246146220.html')
        clean_text = get_morth_raw(html)
        morph = pymorphy2.MorphAnalyzer()
        spl = split_by_words(morph, clean_text)
        print(spl)


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.split(dir_path)[0])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
