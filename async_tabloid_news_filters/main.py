import asyncio
import logging
from functools import partial
import async_timeout
import pymorphy2
from aiohttp import ClientSession, web
from aiohttp.client_exceptions import ClientConnectorError, InvalidURL

from adapters.exceptions import ArticleNotFoundError
from adapters.inosmi_ru import sanitize_article_text
from tools.helpers import ProcessingStatus
from tools.helpers import UrlLimitError
from tools.helpers import create_handy_nursery
from tools.helpers import measure_execution_time
from tools.helpers import fetch
from tools.helpers import get_args_parser
from tools.helpers import get_charged_words
from tools.helpers import read_from_cache, write_to_cache
from tools.text_tools import calculate_jaundice_rate
from tools.text_tools import split_by_words


async def get_article_text_by_url(article_url, _timeout):
    async with async_timeout.timeout(_timeout):
        async with ClientSession() as session:
            return await fetch(session, article_url)


def add_to_results_dict(raw_data_sets):
    for data_set in raw_data_sets:
        _url, status, jaundice_rate, word_count = data_set.result()
        results_dict = ({'status': status.value,
                         'url': _url,
                         'score': jaundice_rate,
                         'words_count': word_count})
        logging.info(f' {results_dict=}')
        yield results_dict


async def process_article(article_url, charged_words, morph):
    jaundice_rate = word_count = None
    _timeout = 5
    try:
        status = ProcessingStatus.OK
        html_content = await get_article_text_by_url(article_url, _timeout)
        clean_text = sanitize_article_text(html_content)
        async with measure_execution_time(_timeout):
            async with async_timeout.timeout(_timeout):
                article_words = await split_by_words(morph, clean_text)
        jaundice_rate = calculate_jaundice_rate(article_words, charged_words)
        word_count = len(article_words)
    except (ClientConnectorError, InvalidURL):
        status = ProcessingStatus.FETCH_ERROR
    except ArticleNotFoundError:
        status = ProcessingStatus.PARSING_ERROR
    except (TimeoutError, asyncio.TimeoutError):
        status = ProcessingStatus.TIMEOUT
    return article_url, status, jaundice_rate, word_count


async def process_articles(article_urls, charged_words, morph):
    parallel_tasks = list()
    async with create_handy_nursery() as nursery:
        for article_url in article_urls:
            parallel_tasks.append(nursery.start_soon(process_article(
                article_url, charged_words, morph)))
            raw_data_sets, _ = await asyncio.wait(parallel_tasks)
    return list(add_to_results_dict(raw_data_sets))


async def get_handler(charged_words, morph, redis_host, redis_port, use_cache, request):
    memo_results = list()
    try:
        article_urls = request.query['urls'].split(',')
        if len(article_urls) > 10:
            raise UrlLimitError
        if use_cache:
            memo_results = [await read_from_cache(
                _url, redis_host, redis_port) for _url in article_urls]

        memo_article_urls = [res['url'] for res in memo_results if res]
        urls_to_process = list(set(article_urls) ^ set(memo_article_urls))

        if urls_to_process:
            async with create_handy_nursery() as nursery:
                handler_results = await nursery.start_soon(
                    process_articles(urls_to_process, charged_words, morph))
                if all([handler_results, use_cache]):
                    for process_res in handler_results:
                        await nursery.start_soon(write_to_cache(process_res,
                                                                redis_host,
                                                                redis_port))
                memo_results.extend(handler_results)
        return web.json_response([res for res in memo_results if res])

    except KeyError:
        return web.json_response(data={'ERROR': 'no urls'}, status=400)

    except UrlLimitError:
        return web.json_response(
            data={'ERROR': 'too many urls in request, should be 10 or less'},
            status=400)


def main():
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('pymorphy2.opencorpora_dict.wrapper').setLevel(logging.ERROR)
    charged_words = get_charged_words('charged_dict')
    morph = pymorphy2.MorphAnalyzer()
    args = get_args_parser().parse_args()
    handler = partial(get_handler, charged_words, morph,
                      args.redis_host, args.redis_port, args.use_cache)
    app = web.Application()
    app.add_routes([web.get('/', handler)])
    web.run_app(app=app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()