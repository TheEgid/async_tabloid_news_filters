import json
import sys
from functools import partial

import pymorphy2
import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

sys.path.extend(['../tools', '../adapters', '.', '..'])

from helpers import get_charged_words
from helpers import ProcessingStatus
from main import get_handler


TEST_ARTICLES = [
    'https://inosmi.ru/economic/20191101/246146220.html',
    'https://inosmi.ru/politic/20191030/246128347.html',
    'https://inosmi.ru/politic/20191101/246151423.html',
    'https://inosmi.ru/politic/20191101/246150929.html',
    'https://inosmi.ru/economic/20190629/245384784.html',
    'https://inosmi.ru/politic/20191108/246190685.html',
    'https://plantarum.livejournal.com/473023.html',
    'https://dvmn.org/filer/canonical/1561832205/162/',
    'https://inosmi.ru/politic/20191108/246190685.html',
    'https://plantarum.livejournal.com/473023.html',
    'https://dvmn.org/filer/canonical/1561832205/162/'
]


@pytest.fixture
def charged_words_fixture():
    return get_charged_words('../charged_dict')


@pytest.fixture
def morph_fixture():
    return pymorphy2.MorphAnalyzer()


@pytest.mark.server
class TestApp(AioHTTPTestCase):
    async def get_application(self):
        handler = partial(get_handler, charged_words_fixture, morph_fixture)
        app = web.Application()
        app.router.add_get('/', handler)
        return app

    @unittest_run_loop
    async def test_no_urls(self):
        resp = await self.client.request("GET", "")
        self.assertTrue(resp.status == 400)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)
        self.assertEqual(handler_results['error'], 'no urls')

    @unittest_run_loop
    async def test_too_many_urls(self):
        link = f"?urls={','.join(TEST_ARTICLES)}"
        resp = await self.client.request("GET", link)
        self.assertTrue(resp.status == 400)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)
        self.assertEqual(handler_results['error'], "too many urls in request, should be 10 or less")

    @unittest_run_loop
    async def test_bad_url(self):
        link = f"?urls={TEST_ARTICLES[6]}"
        resp = await self.client.request("GET", link)
        self.assertTrue(resp.status == 200)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)[0]
        status = ProcessingStatus.PARSING_ERROR
        self.assertEqual(handler_results['status'], status.value)
        self.assertEqual(handler_results['url'], TEST_ARTICLES[6])
        self.assertEqual(handler_results['score'], None)
        self.assertEqual(handler_results['words_count'], None)