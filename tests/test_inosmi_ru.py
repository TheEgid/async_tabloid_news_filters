import sys
import unittest

import pytest
import requests

sys.path.append('../adapters')
from inosmi_ru import ArticleNotFoundError
from inosmi_ru import HeaderNotFoundError
from inosmi_ru import sanitize_article_header
from inosmi_ru import sanitize_article_text

link = 'https://inosmi.ru/economic/20190629/245384784.html'

@pytest.mark.adapters_inosmi_ru
class TestInosmiRu(unittest.TestCase):

    def test_sanitize_article_header(self):
        resp = requests.get(link)
        resp.raise_for_status()
        clean_header = sanitize_article_header(resp.text)
        self.assertFalse(clean_header.startswith('<h1>'))
        self.assertFalse(clean_header.endswith('</h1>'))

    def test_sanitize_article_text(self):
        resp = requests.get(link)
        resp.raise_for_status()

        clean_text = sanitize_article_text(resp.text)
        clean_plaintext = sanitize_article_text(resp.text, plaintext=True)

        # self.assertTrue(clean_text.startswith('<article>'))
        # self.assertTrue(clean_text.endswith('</article>'))
        self.assertIn('В субботу, 29 июня, президент США Дональд Трамп', clean_text)
        self.assertIn('За несколько часов до встречи с Си', clean_text)
        self.assertIn('<img src="', clean_text)
        self.assertIn('<a href="', clean_text)
        self.assertIn('<h1>', clean_text)
        self.assertIn('В субботу, 29 июня, президент США Дональд Трамп', clean_plaintext)
        self.assertIn('За несколько часов до встречи с Си', clean_plaintext)
        self.assertNotIn('<img src="', clean_plaintext)
        self.assertNotIn('<a href="', clean_plaintext)
        self.assertNotIn('<h1>', clean_plaintext)
        self.assertNotIn('</article>', clean_plaintext)
        self.assertNotIn('<h1>', clean_plaintext)

    def test_wrong_url(self):
        resp = requests.get('http://example.com')
        resp.raise_for_status()
        with self.assertRaises(ArticleNotFoundError):
            sanitize_article_text(resp.text)

    def test_should_be_header_on_page(self):
        resp = requests.get('https://raw.githubusercontent.com/psf/requests/master/requests/api.py')
        resp.raise_for_status()
        with self.assertRaises(HeaderNotFoundError):
            sanitize_article_header(resp)
