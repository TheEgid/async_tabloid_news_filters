import unittest
import pytest
import requests
from adapters import SANITIZERS
from adapters import ArticleNotFound, HeaderNotFound

sanitize_article_text, sanitize_article_header = SANITIZERS["inosmi_ru"]

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

    def test_wrong_url(self):
        resp = requests.get('http://example.com')
        with self.assertRaises(ArticleNotFound):
            resp.raise_for_status()
            sanitize_article_text(resp.text)

    def test_should_be_header_on_page(self):
        resp = requests.get('https://raw.githubusercontent.com/psf/requests/master/requests/api.py')
        with self.assertRaises(HeaderNotFound):
            resp.raise_for_status()
            sanitize_article_header(resp)
