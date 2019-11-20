import argparse
import asyncio
import contextlib
import logging
import os
import sys
import pickle
import time
from enum import Enum
import aionursery
import aioredis
from aiohttp.client_exceptions import ClientResponseError

sys.path.extend(['./tools', './adapters', '.', '..'])

from inosmi_ru import ArticleNotFoundError


class UrlLimitError(Exception):
    pass


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def read_from_cache(url, host, port):
    redis = await aioredis.create_redis((host, port))
    try:
        val = await redis.get(url)
        data = pickle.loads(val)
        logging.info(' READ REDIS CACHE DATA')
        return data
    except (TypeError, aioredis.RedisError, asyncio.CancelledError):
        return None
    finally:
        redis.close()
        await redis.wait_closed()


async def write_to_cache(data, host, port):
    redis = await aioredis.create_redis((host, port))
    try:
        if data['status'] == 'OK':
            await redis.set(data['url'], pickle.dumps(data))
            logging.info(' WRITE REDIS CACHE DATA')
    except (TypeError, aioredis.RedisError):
        return None
    finally:
        redis.close()
        await redis.wait_closed()


async def fetch(session, url):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()
    except ClientResponseError:
        raise ArticleNotFoundError


@contextlib.asynccontextmanager
async def create_handy_nursery():
    try:
        async with aionursery.Nursery() as nursery:
            yield nursery
    except aionursery.MultiError as e:
        if len(e.exceptions) == 1:
            raise e.exceptions[0]
        raise


@contextlib.asynccontextmanager
async def execution_timer():
    _timeout = 3
    async with create_handy_nursery() as nursery:
        start = time.monotonic()
        yield nursery
        end = time.monotonic() - start
        if end > _timeout:
            raise asyncio.TimeoutError
        logging.info(' Analyzed in {:.2f} sec'.format(end))


def get_charged_words(folder_name):
    files = os.listdir('./' + folder_name)
    words = list()
    for file in files:
        if file.endswith('txt'):
            _filepath = f'{folder_name}/{file}'
            with open(_filepath, encoding='utf8') as f:
                words.extend([line.strip() for line in f.readlines()])
    return words


def get_args_parser():
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=formatter_class)
    parser.add_argument('-host', default='localhost')
    parser.add_argument('-port', type=int, default=80)
    parser.add_argument('-redis_host', default='localhost')
    parser.add_argument('-redis_port', type=int, default=6379)
    parser.add_argument('-use_cache', action='store_true', default=False,
                        help='Redis cache ON/OFF checker')
    return parser
