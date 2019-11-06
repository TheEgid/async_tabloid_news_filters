import asyncio
import logging
import os

import aiofiles
import aiohttp
import pymorphy2
from adapters import SANITIZERS
from aiohttp import web
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


async def process_article(article_url, charged_words, morph):
    clean_text_header = jaundice_rate = len_article_words = None
    try:
        status = ProcessingStatus.OK
        html_content = await get_article_text_by_url(article_url)
        clean_text_header, clean_text = get_clean_data(html_content)
        async with execution_timer():
            article_words = await split_by_words(morph, clean_text)
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


async def start_process_article(article_url, charged_words, morph):
    parallel_tasks = list()
    async with create_handy_nursery() as nursery:
        parallel_tasks.append(nursery.start_soon(process_article(
            article_url, charged_words, morph)))
        raw_results, _ = await asyncio.wait(parallel_tasks)
        return [raw_result.result() for raw_result in raw_results]


async def handler(article_url, charged_words, morph):
    result = await start_process_article(article_url, charged_words, morph)
    status, text_header, jaundice_rate, len_article_words = result[0]
    logging.info(f'Заголовок: {text_header} Статус: {status.value} '
                 f'Рейтинг: {jaundice_rate} Слов в статье: {len_article_words}')
    return {
        "status": status.value,
        "url": article_url,
        "score": jaundice_rate,
        "words_count": len_article_words,
    }


async def get_handler(request):
    charged_words = await get_charged_words('charged_dict')
    morph = pymorphy2.MorphAnalyzer()
    rez_list = list()
    key = 'urls'
    params = request.query[key]
    values = params.split(',')
    for article_url in values:
        rez = await handler(article_url, charged_words, morph)
        rez_list.append(rez)
    return web.json_response(rez_list)


def run_server(host="127.0.0.1", port=80):
    app = web.Application()
    app.add_routes([web.get('/', get_handler)])
    web.run_app(app=app, host=host, port=port)

#
# async def main():
#
#     for article_url in TEST_ARTICLES:
#         r = await handler(article_url)
#         print(r)



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(
        logging.ERROR)

    run_server()

#http://127.0.0.1/?urls=https://inosmi.ru/economic/20190629/245384784.html,https://inosmi.ru/economic/20191101/246146220.html,https://9__9.com%27

    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(main())







