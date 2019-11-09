import asyncio
import logging
from functools import partial

import aiohttp
import pymorphy2
from adapters.inosmi_ru import ArticleNotFoundError
from adapters.inosmi_ru import HeaderNotFoundError
from adapters.inosmi_ru import sanitize_article_header
from adapters.inosmi_ru import sanitize_article_text
from aiohttp import web
from aiohttp.client_exceptions import ClientConnectorError
from async_timeout import timeout
from tools.helpers import ProcessingStatus
from tools.helpers import UrlsLimitError
from tools.helpers import create_handy_nursery
from tools.helpers import execution_timer
from tools.helpers import fetch
from tools.helpers import get_args_parser
from tools.helpers import get_charged_words
from tools.text_tools import calculate_jaundice_rate
from tools.text_tools import split_by_words


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
    text_header = jaundice_rate = len_article_words = None
    try:
        status = ProcessingStatus.OK
        html_content = await get_article_text_by_url(article_url)
        text_header, clean_text = get_clean_data(html_content)
        async with execution_timer():
            article_words = await split_by_words(morph, clean_text)
        jaundice_rate = calculate_jaundice_rate(article_words, charged_words)
        len_article_words = len(article_words)
    except ClientConnectorError:
        status = ProcessingStatus.FETCH_ERROR
    except (ArticleNotFoundError, HeaderNotFoundError):
        status = ProcessingStatus.PARSING_ERROR
    except (TimeoutError, asyncio.TimeoutError):
        status = ProcessingStatus.TIMEOUT
    return article_url, status, text_header, jaundice_rate, len_article_words


async def handler_helper(article_urls, charged_words, morph):
    parallel_tasks = list()
    async with create_handy_nursery() as nursery:
        for article_url in article_urls:
            parallel_tasks.append(nursery.start_soon(process_article(
                article_url, charged_words, morph)))
            raw_results, _ = await asyncio.wait(parallel_tasks)
            results = [x.result() for x in raw_results]

    handler_result = list()
    for result in results:
        _url, status, text_header, jaundice_rate, len_article_words = result
        logging.info(f'Заголовок: {text_header} '
                     f'Статус: {status.value} '
                     f'Рейтинг: {jaundice_rate} '
                     f'Слов в статье: {len_article_words}')
        result_dict = {
            "status": status.value,
            "url": _url,
            "score": jaundice_rate,
            "words_count": len_article_words,
        }
        handler_result.append(result_dict)
    return handler_result


async def get_handler(charged_words, morph, request):
    try:
        _article_urls = request.query['urls']
        article_urls = _article_urls.split(',')
        if len(article_urls) > 10:
            raise UrlsLimitError

        async with create_handy_nursery() as nursery:
            rez_data = await nursery.start_soon(
                handler_helper(article_urls, charged_words, morph))
        return web.json_response(rez_data)

    except KeyError:
        return web.json_response(data={
            'error': 'no urls'},
            status=400)

    except UrlsLimitError:
        return web.json_response(data={
            'error': 'too many urls in request, should be 10 or less'},
            status=400)


def run_server(host='0.0.0.0', port=80):
    charged_words = get_charged_words('charged_dict')
    morph = pymorphy2.MorphAnalyzer()
    handler = partial(get_handler, charged_words, morph)
    app = web.Application()
    app.add_routes([web.get('/', handler)])
    web.run_app(app=app, host=host, port=port)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)
    parser = get_args_parser()
    args = parser.parse_args()
    run_server(port=args.port)

# http://127.0.0.1/?urls=https://inosmi.ru/economic/20190629/245384784.html,https://inosmi.ru/economic/20191101/246146220.html,https://9__9.com%27