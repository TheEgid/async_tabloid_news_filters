import asyncio
import logging
import os
import sys
from functools import partial

import pymorphy2
from aiohttp import ClientSession, web
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout

sys.path.extend(['./tools', './adapters'])

from inosmi_ru import ArticleNotFoundError
from inosmi_ru import HeaderNotFoundError
from inosmi_ru import sanitize_article_header
from inosmi_ru import sanitize_article_text

from helpers import ProcessingStatus
from helpers import UrlsLimitError
from helpers import create_handy_nursery
from helpers import execution_timer
from helpers import fetch
from helpers import get_args_parser
from helpers import get_charged_words
from helpers import RedisCache, read_from_cashe, write_to_cashe
from text_tools import calculate_jaundice_rate
from text_tools import split_by_words


def get_clean_data(_html):
    clean_text_header = sanitize_article_header(_html)
    clean_text = sanitize_article_text(_html)
    return clean_text_header, clean_text


async def get_article_text_by_url(article_url):
    _timeout = 3
    async with timeout(_timeout):
        async with ClientSession() as session:
            return await fetch(session, article_url)


async def process_article(article_url, charged_words, morph):
    text_header = jaundice_rate = word_count = None
    try:
        status = ProcessingStatus.OK
        html_content = await get_article_text_by_url(article_url)
        text_header, clean_text = get_clean_data(html_content)
        async with execution_timer():
            article_words = await split_by_words(morph, clean_text)
        jaundice_rate = calculate_jaundice_rate(article_words, charged_words)
        word_count = len(article_words)
    except ClientConnectorError:
        status = ProcessingStatus.FETCH_ERROR
    except (ArticleNotFoundError, HeaderNotFoundError):
        status = ProcessingStatus.PARSING_ERROR
    except (TimeoutError, asyncio.TimeoutError):
        status = ProcessingStatus.TIMEOUT
    return article_url, status, text_header, jaundice_rate, word_count


async def handler_helper(article_urls, charged_words, morph):

    handler_results = list()
    parallel_tasks = list()
    async with create_handy_nursery() as nursery:
        for article_url in article_urls:
            parallel_tasks.append(nursery.start_soon(process_article(
                article_url, charged_words, morph)))
            raw_data_sets, _ = await asyncio.wait(parallel_tasks)
            data_sets = [data_set.result() for data_set in raw_data_sets]

    for data_set in data_sets:
        _url, status, text_header, jaundice_rate, word_count = data_set
        results = {"status": status.value,
                   "url": _url,
                   "score": jaundice_rate,
                   "words_count": word_count}
        handler_results.append(results)
        logging.info(f'Header: {text_header} - {results=}')
    return handler_results


async def get_handler(charged_words, morph, request):
    try:
        article_urls = request.query['urls'].split(',')
        if len(article_urls) > 10:
            raise UrlsLimitError
        memo_results = list(filter(
            None, [read_from_cashe(url, redis_cache) for url in article_urls]))
        memo_article_urls = [memo_result['url'] for memo_result in memo_results]
        if memo_article_urls:
            logging.info('USED REDIS CACHE DATA')
        urls_to_process = list(set(article_urls) ^ set(memo_article_urls))
        if urls_to_process:
            async with create_handy_nursery() as nursery:
                handler_results = await nursery.start_soon(
                    handler_helper(urls_to_process, charged_words, morph))
            if handler_results:
                [write_to_cashe(process_result, redis_cache) for
                 process_result in handler_results]
                memo_results.extend(handler_results)
        return web.json_response(memo_results)
    except KeyError:
        return web.json_response(data={
            'error': 'no urls'},
            status=400)
    except UrlsLimitError:
        return web.json_response(data={
            'error': 'too many urls in request, should be 10 or less'},
            status=400)


def run_server(host, port):
    charged_words = get_charged_words('charged_dict')
    morph = pymorphy2.MorphAnalyzer()
    handler = partial(get_handler, charged_words, morph)
    app = web.Application()
    app.add_routes([web.get('/', handler)])
    web.run_app(app=app, host=host, port=port)


if __name__ == '__main__':
    dir_path = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.split(dir_path)[0])
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)
    args = get_args_parser().parse_args()
    redis_cache = RedisCache(args.redis_host, args.redis_port)
    run_server(host=args.host, port=args.port)

# http://127.0.0.1/?urls=https://inosmi.ru/economic/20190629/245384784.html,https://inosmi.ru/economic/20191101/246146220.html,https://9__9.com%27