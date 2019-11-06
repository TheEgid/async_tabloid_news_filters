import asyncio
import contextlib
import logging
import time
from enum import Enum

import aionursery


class ProcessingStatus(Enum):
    OK = 'OK'
    FETCH_ERROR = 'FETCH_ERROR'
    PARSING_ERROR = 'PARSING_ERROR'
    TIMEOUT = 'TIMEOUT'


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
