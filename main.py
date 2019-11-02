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


dictionary_words = ['разрушение', 'бомба', 'пожар', 'погибший', 'глобальный',
                 'ресурс', 'выступать', 'ошибка', 'угроза', 'противопоставлять',
                 'предостережение']


async def get_article_text():
    async with aiohttp.ClientSession() as session:
        html = await fetch(session,
                           'https://inosmi.ru/economic/20191101/246146220.html')
        return get_morth_raw(html)


async def process_article():
    clean_text = await get_article_text()
    morph = pymorphy2.MorphAnalyzer()
    article_words = split_by_words(morph, clean_text)

    print(article_words)
    jaundice_rate = calculate_jaundice_rate(article_words, dictionary_words)
    print(f'Рейтинг: {jaundice_rate}\nСлов в статье: {len(article_words)}')



async def main():
    await process_article()


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.split(dir_path)[0])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
