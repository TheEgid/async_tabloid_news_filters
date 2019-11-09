import argparse
import asyncio
import contextlib
import logging
import os
import time
from enum import Enum

import aionursery


class UrlsLimitError(Exception):
    pass


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.text()


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
        logging.info('Анализ закончен за {:.2f} сек'.format(end))


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
    parser.add_argument('-p', '--port', type=int,
                        default=80, help='connection port')
    return parser
