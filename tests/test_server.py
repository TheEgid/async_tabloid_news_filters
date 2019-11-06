import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

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


@pytest.fixture
def link():
    yield 'http://selenium1py.pythonanywhere.com/'


class MyAppTestCase(AioHTTPTestCase):

    async def get_application(self):
        async def get_handler(request):
            key = 'urls'
            params = request.query[key]
            values = params.split(',')
            return web.json_response({key: values})
        app = web.Application()
        app.router.add_get('/', get_handler)
        return app

    @pytest.mark.parametrize('link')
    @unittest_run_loop
    async def test_example(self, link):
        resp = await self.client.request("GET", link)
        assert resp.status == 200
        result = await resp.json()
        print(result)
        self.assertDictEqual(
            {'urls':
                 ['https://ya.ru', 'https://google.com']
             },
            result)


#
# class MyAppTestCase(AioHTTPTestCase):
#
#     async def get_application(self):
#         async def get_handler(request):
#             key = 'urls'
#             params = request.query[key]
#             values = params.split(',')
#             return web.json_response({key: values})
#         app = web.Application()
#         app.router.add_get('/', get_handler)
#         return app
#
#     @unittest_run_loop
#     async def test_example(self):
#         resp = await self.client.request("GET", "?urls=https://ya.ru,https://google.com")
#         assert resp.status == 200
#         result = await resp.json()
#         print(result)
#         self.assertDictEqual(
#             {'urls':
#                  ['https://ya.ru', 'https://google.com']
#              },
#             result)
