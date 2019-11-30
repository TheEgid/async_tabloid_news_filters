import json
from functools import partial
import pymorphy2
import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from tools.helpers import get_args_parser
from tools.helpers import get_charged_words
from tools.helpers import ProcessingStatus
from main import handle_request


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


@pytest.mark.server
class TestApp(AioHTTPTestCase):

    def setUp(self):
        args = get_args_parser().parse_args([])
        self.charged_words = get_charged_words('./charged_dict')
        self.morph = pymorphy2.MorphAnalyzer()
        self.redis_host = args.redis_host
        self.redis_port = args.redis_port
        self.use_cache = args.use_cache
        super().setUp()

    async def get_application(self):
        handler = partial(handle_request, self.charged_words, self.morph,
                          self.redis_host, self.redis_port, self.use_cache)
        app = web.Application()
        app.router.add_get('/', handler)
        return app

    @unittest_run_loop
    async def test_process_few_urls_at_once(self):
        _links = ','.join(TEST_ARTICLES[:5])
        links = f"?urls={_links}"
        resp = await self.client.request("GET", links)
        self.assertTrue(resp.status == 200)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)
        self.assertTrue(all(
            [result['status'] == ProcessingStatus.OK.value for result in
             handler_results]))
        _urls = [x['url'] for x in handler_results]
        self.assertSetEqual(set(TEST_ARTICLES[:5]), set(_urls))
        self.assertTrue(all(
            [isinstance(result['words_count'], int) for result in
             handler_results]))
        self.assertTrue(all(
            [isinstance(result['score'], float) for result in handler_results]))

    @unittest_run_loop
    async def test_process_few_urls_by_chain(self):
        for link in TEST_ARTICLES[:5]:
            resp = await self.client.request("GET", f"?urls={link}")
            self.assertTrue(resp.status == 200)
            resp_text = await resp.text()
            handler_results = json.loads(resp_text)[0]
            self.assertEqual(handler_results['status'],
                             ProcessingStatus.OK.value)
            self.assertEqual(link, handler_results['url'])
            self.assertTrue(isinstance(handler_results['words_count'], int))
            self.assertTrue(isinstance(handler_results['score'], float))

    @unittest_run_loop
    async def test_process_no_urls(self):
        resp = await self.client.request("GET", "")
        self.assertTrue(resp.status == 400)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)
        self.assertEqual(handler_results['ERROR'], 'no urls')

    @unittest_run_loop
    async def test_process_too_many_urls(self):
        link = f"?urls={','.join(TEST_ARTICLES)}"
        resp = await self.client.request("GET", link)
        self.assertTrue(resp.status == 400)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)
        self.assertEqual(handler_results['ERROR'], "too many urls in request, should be 10 or less")

    @unittest_run_loop
    async def test_process_unknown_url(self):
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

    @unittest_run_loop
    async def test_process_one_url(self):
        link = TEST_ARTICLES[2]
        resp = await self.client.request("GET", f"?urls={link}")
        self.assertTrue(resp.status == 200)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)[0]
        self.assertEqual(handler_results['status'], ProcessingStatus.OK.value)
        self.assertEqual(link, handler_results['url'])
        self.assertTrue(isinstance(handler_results['words_count'], int))
        self.assertTrue(isinstance(handler_results['score'], float))

    @unittest_run_loop
    async def test_process_invalid_url(self):
        invalid_url = 'invalid_url'
        link = f"?urls={invalid_url}"
        resp = await self.client.request("GET", link)
        self.assertTrue(resp.status == 200)
        resp_text = await resp.text()
        handler_results = json.loads(resp_text)[0]
        status = ProcessingStatus.FETCH_ERROR
        self.assertEqual(handler_results['status'], status.value)
        self.assertEqual(handler_results['url'], invalid_url)
        self.assertEqual(handler_results['score'], None)
        self.assertEqual(handler_results['words_count'], None)