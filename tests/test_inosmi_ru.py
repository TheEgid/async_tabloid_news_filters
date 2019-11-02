import unittest
import pytest
import requests
import sys
sys.path.append('..')
from adapters.inosmi_ru import sanitize
from adapters.exceptions import ArticleNotFound


@pytest.mark.adapters_inosmi_ru
class TestInosmiRu(unittest.TestCase):
    def test_sanitize(self):
        link = 'https://inosmi.ru/economic/20190629/245384784.html'
        resp = requests.get(link)
        resp.raise_for_status()
        clean_text = sanitize(resp.text)
        clean_plaintext = sanitize(resp.text, plaintext=True)

        self.assertTrue(clean_text.startswith('<article>'))
        self.assertTrue(clean_text.endswith('</article>'))
        self.assertTrue('В субботу, 29 июня, президент США Дональд Трамп'
                        in clean_text)
        self.assertTrue('За несколько часов до встречи с Си' in clean_text)
        self.assertTrue('<img src="' in clean_text)
        self.assertTrue('<a href="' in clean_text)
        self.assertTrue('<h1>' in clean_text)

        self.assertTrue('В субботу, 29 июня, президент США Дональд Трамп'
                        in clean_plaintext)
        self.assertTrue('За несколько часов до встречи с Си' in clean_plaintext)
        self.assertTrue('<img src="' not in clean_plaintext)
        self.assertTrue('<a href="' not in clean_plaintext)
        self.assertTrue('<h1>' not in clean_plaintext)
        self.assertTrue('</article>' not in clean_plaintext)
        self.assertTrue('<h1>' not in clean_plaintext)

    def test_sanitize_wrong_url(self):
        resp = requests.get('http://example.com')
        resp.raise_for_status()
        with self.assertRaises(ArticleNotFound):
            sanitize(resp.text)
