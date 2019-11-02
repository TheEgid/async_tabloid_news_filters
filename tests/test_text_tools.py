import pymorphy2
import pytest
import unittest
from text_tools import split_by_words
from text_tools import calculate_jaundice_rate
from text_tools import has_latin_letters


@pytest.mark.text_tools
class TestTextTools(unittest.TestCase):
    def test_has_latin_letters(self):
        case = tuple(map(has_latin_letters, ('string', 'stringЮ', 'Проверка1')))
        self.assertTupleEqual(case, (True, True, False))

    def test_split_by_words(self):
        # Экземпляры MorphAnalyzer занимают 10-15Мб RAM т.к. загружают в память много данных
        # Старайтесь ораганизовать свой код так, чтоб создавать экземпляр MorphAnalyzer заранее и в единственном числе
        morph = pymorphy2.MorphAnalyzer()

        self.assertListEqual(split_by_words(
            morph,  'Во-первых, он хочет, чтобы'),
            ['во-первых', 'хотеть', 'чтобы'])

        self.assertListEqual(split_by_words(
            morph, '«Удивительно, но это стало началом!»'),
            ['удивительно', 'это', 'стать', 'начало'])

    def test_calculate_jaundice_rate(self):
        self.assertTrue(-0.01 < calculate_jaundice_rate([], []) < 0.01)
        self.assertTrue(33.0 < calculate_jaundice_rate(
            ['все', 'аутсайдер', 'побег'],['аутсайдер', 'банкротство']) < 34.0)
