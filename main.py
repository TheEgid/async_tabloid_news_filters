import aiohttp
import asyncio
import pymorphy2
import aiofiles
import os
import sys

from helpers import create_handy_nursery
from text_tools import split_by_words
from text_tools import calculate_jaundice_rate
from adapters import SANITIZERS


TEST_ARTICLES = [
    'https://inosmi.ru/economic/20191101/246146220.html',
    'https://inosmi.ru/politic/20191030/246128347.html',
    'https://inosmi.ru/politic/20191101/246151423.html',
    'https://inosmi.ru/politic/20191101/246150929.html',
    'https://inosmi.ru/economic/20190629/245384784.html',
]


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def get_morth_raw(_html):
    sanitize = SANITIZERS["inosmi_ru"]
    clean_text_header, clean_text = sanitize(_html)
    return clean_text_header, clean_text


async def get_article_text(article_url):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, article_url)
        return get_morth_raw(html)


async def process_article(article_url):
    clean_text_header, clean_text = await get_article_text(article_url)
    morph = pymorphy2.MorphAnalyzer()
    article_words = split_by_words(morph, clean_text)
    negative_words = await handle_index_page(r'charged_dict\negative_words.txt')
    jaundice_rate = calculate_jaundice_rate(article_words, negative_words)
    return clean_text_header, jaundice_rate, len(article_words)


async def handle_index_page(filepath):
    async with aiofiles.open(filepath, mode='r', encoding='utf8') as f:
        return [line.strip() for line in await f.readlines()]


async def main():
    _queue = list()

    async with create_handy_nursery() as nursery:
        for article_url in TEST_ARTICLES:
            _queue.append(
                nursery.start_soon(process_article(article_url)))
            raw_results, _ = await asyncio.wait(_queue)

    for raw_result in raw_results:
        clean_text_header, jaundice_rate, article_words = raw_result.result()
        print(f'\nЗаголовок: {clean_text_header}\n'
              f'Рейтинг: {jaundice_rate}\n'
              f'Слов в статье: {article_words}\n')


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.split(dir_path)[0])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
