
from main import run_server

# https://aiohttp.readthedocs.io/en/stable/testing.html

TEST_ARTICLES = [
    'https://inosmi.ru/economic/20191101/246146220.html',
    'https://inosmi.ru/politic/20191030/246128347.html',
    'https://inosmi.ru/politic/20191101/246151423.html',
    'https://inosmi.ru/politic/20191101/246150929.html',
    'https://inosmi.ru/economic/20190629/245384784.html',
    'https://9__9.com',
    'https://inosmi.ru/politic/20191108/246190685.html'
    'https://plantarum.livejournal.com/473023.html',
    'https://dvmn.org/filer/canonical/1561832205/162/'
]

import aionursery
import asyncio
import asynctest
import contextlib
import unittest
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from aiohttp import web


@contextlib.asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        raise


async def say(what, when):
    await asyncio.sleep(when)
    print(what)
    return what


class TestAsyncMain(asynctest.TestCase):

    async def test_say(self):
        async with create_handy_nursery() as nursery:
            case = await nursery.start_soon(say('Privet!', 0))
            print(case)
        self.assertNotEqual('qPrivet!', case)
        self.assertEqual('Privet!', case)


class MyAppTestCase(AioHTTPTestCase):

    async def get_application(self):
        #run_server()
        # async def hello(request):
        #     return web.Response(text='Hello, world')

        app = web.Application()
        app.router.add_get('/', run_server)

        return app

    @unittest_run_loop
    async def test_example(self):
        resp = await self.client.request("GET", "/")

        print(resp.status)
        self.assertTrue(resp.status == 200)
        text = await resp.text()
        print(text)
        breakpoint()
        self.assertIn("Hello, world", text)


if __name__ == '__main__':
    unittest.main()

# https://aiohttp.readthedocs.io/en/stable/web_advanced.html


# async def shutdown(server, app, handler):

#    server.close()
#    await server.wait_closed()
#    app.client.close()  # database connection close
#    await app.shutdown()
#    await handler.finish_connections(10.0)
#    await app.cleanup()


# self.assertDictEqual(
        #     {'urls':
        #          ['https://ya.ru', 'https://google.com']
        #      },
        #     result)
        #self.loop.run_until_complete(test_get_route())