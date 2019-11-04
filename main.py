import asyncio
import os
import sys

import aiofiles
import aiohttp
import pymorphy2
from adapters import SANITIZERS
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
from helpers import ProcessingStatus
from helpers import create_handy_nursery
from helpers import execution_timer
from text_tools import calculate_jaundice_rate
from text_tools import split_by_words

sanitize_article_text, sanitize_article_header, \
ArticleNotFound, HeaderNotFound = SANITIZERS["inosmi_ru"]


TEST_ARTICLES = [
    'https://inosmi.ru/economic/20191101/246146220.html',
    'https://inosmi.ru/politic/20191030/246128347.html',
    'https://inosmi.ru/politic/20191101/246151423.html',
    'https://inosmi.ru/politic/20191101/246150929.html',
    'https://inosmi.ru/economic/20190629/245384784.html',
    'https://9__9.com',
    'https://plantarum.livejournal.com/473023.html',
    'https://dvmn.org/filer/canonical/1561832205/162/'
]


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


def get_clean_data(_html):
    clean_text_header = sanitize_article_header(_html)
    clean_text = sanitize_article_text(_html)
    return clean_text_header, clean_text


async def get_article_text_by_url(article_url):
    _timeout = 3
    async with timeout(_timeout):
        async with aiohttp.ClientSession() as session:
            return await fetch(session, article_url)


async def process_article(article_url):
    clean_text_header = jaundice_rate = len_article_words = None
    try:
        status = ProcessingStatus.OK
        html_content = await get_article_text_by_url(article_url)
        clean_text_header, clean_text = get_clean_data(html_content)
        morph = pymorphy2.MorphAnalyzer()
        async with execution_timer():
            article_words = await split_by_words(morph, clean_text)
        charged_words = await get_charged_words('charged_dict')
        jaundice_rate = calculate_jaundice_rate(article_words, charged_words)
        len_article_words = len(article_words)
    except ClientConnectorError:
        status = ProcessingStatus.FETCH_ERROR
    except (ArticleNotFound, HeaderNotFound):
        status = ProcessingStatus.PARSING_ERROR
    except (TimeoutError, asyncio.TimeoutError):
        status = ProcessingStatus.TIMEOUT
    return status, clean_text_header, jaundice_rate, len_article_words


async def get_charged_words(folder_name):
    files = os.listdir('./' + folder_name)
    words = list()
    for file in files:
        if file.endswith('txt'):
            _filepath = f'{folder_name}/{file}'
            async with aiofiles.open(_filepath, mode='r', encoding='utf8') as f:
                words.extend([line.strip() for line in await f.readlines()])
    return words


async def main():
    parallel_tasks = list()
    async with create_handy_nursery() as nursery:
        for article_url in TEST_ARTICLES:
            parallel_tasks.append(nursery.start_soon(process_article(article_url)))
            raw_results, _ = await asyncio.wait(parallel_tasks)

    for raw_result in raw_results:
        status, text_header, jaundice_rate, len_article_words = raw_result.result()
        print(f'\nЗаголовок: {text_header}\n'
              f'Статус: {status.value}\n'
              f'Рейтинг: {jaundice_rate}\n'
              f'Слов в статье: {len_article_words}\n')


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.split(dir_path)[0])
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
