import unittest

import aionursery
import asynctest
import pymorphy2
import pytest
from text_tools import calculate_jaundice_rate
from text_tools import has_latin_letters
from text_tools import split_by_words


@pytest.mark.text_tools
class TestAsyncTextTools(asynctest.TestCase):
    async def test_split_by_words(self):
        # Экземпляры MorphAnalyzer занимают 10-15Мб RAM т.к. загружают в память много данных
        # Старайтесь ораганизовать свой код так, чтоб создавать экземпляр MorphAnalyzer заранее и в единственном числе
        morph = pymorphy2.MorphAnalyzer()
        async with aionursery.Nursery() as nursery:
            case1 = await nursery.start_soon(
                split_by_words(morph,
                               'Во-первых, он хочет, чтобы'))
            case2 = await nursery.start_soon(
                split_by_words(morph, 'удивительно, но это стало началом!'))

        self.assertListEqual(case1,
                             ['во-первых', 'хотеть', 'чтобы'])
        self.assertListEqual(case2,
                             ['удивительно', 'это', 'стать', 'начало'])


@pytest.mark.text_tools
class TestTextTools(unittest.TestCase):
    def test_has_latin_letters(self):
        case = tuple(map(has_latin_letters, ('string', 'stringЮ', 'Проверка1')))
        self.assertTupleEqual(case, (True, True, False))

    def test_calculate_jaundice_rate(self):
        self.assertTrue(-0.01 < calculate_jaundice_rate([], []) < 0.01)
        self.assertTrue(33.0 < calculate_jaundice_rate(
            ['все', 'аутсайдер', 'побег'],['аутсайдер', 'банкротство']) < 34.0)
