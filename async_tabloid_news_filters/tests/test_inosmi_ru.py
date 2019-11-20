import sys
import unittest

import pytest
import requests

sys.path.append('./adapters')
from inosmi_ru import ArticleNotFoundError
from inosmi_ru import sanitize_article_text


class TestInosmiRu(unittest.TestCase):

    def test_sanitize_article_text(self):
        resp = requests.get('https://inosmi.ru/economic/20190629/245384784.html')
        resp.raise_for_status()

        clean_text = sanitize_article_text(resp.text)
        clean_plaintext = sanitize_article_text(resp.text, plaintext=True)

        self.assertTrue(clean_text.startswith('<article>'))
        self.assertTrue(clean_text.endswith('</article>'))
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
