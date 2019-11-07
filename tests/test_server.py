from aiohttp.test_utils import AioHTTPTestCase
from main import run_server

# https://aiohttp.readthedocs.io/en/stable/testing.html

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



class MyAppTestCase(AioHTTPTestCase):

    async def get_application(self):
        # async def get_handler(request):
        #     key = 'urls'
        #     params = request.query[key]
        #     values = params.split(',')
        #     return web.json_response({key: values})
            # charged_words = get_charged_words('../charged_dict')
            # morph = pymorphy2.MorphAnalyzer()
            # handler = partial(get_handler, charged_words, morph)
            # app = web.Application()
            # app.router.add_get('/', handler)
        return run_server()

    # async def tearDown(self):
    #     await self.app.shutdown()
        # Run loop until tasks done:
        #loop.run_until_complete(asyncio.gather(*pending))

    #@unittest_run_loop
    async def test_example_vanilla(self):
        async def test_get_route():
            link = r'?urls=https://ya.ru,https://google.com'
            # async with aionursery.Nursery() as nursery:
            #     resp = await nursery.start_soon(self.client.request("GET", link))
            #     #await asyncio.sleep(0)
            resp = await self.client.request("GET", link)
            assert resp.status == 200
            # print(type(resp))
            # result = await resp.json()
            # print(result)

        #await asyncio.run(test_get_route())
        self.loop.run_until_complete(test_get_route())




        # self.assertDictEqual(
        #     {'urls':
        #          ['https://ya.ru', 'https://google.com']
        #      },
        #     result)
        #self.loop.run_until_complete(test_get_route())