from bs4 import BeautifulSoup
from .exceptions import ArticleNotFound, HeaderNotFound
from .html_tools import remove_buzz_attrs, remove_buzz_tags, remove_all_tags


def sanitize_article_header(html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        header = soup.find('h1', {'class': 'article-header__title'}).text
    except (AttributeError,TypeError):
        raise HeaderNotFound()
    return header


def sanitize_article_text(html, plaintext=False):
    soup = BeautifulSoup(html, 'html.parser')
    articles = soup.select("article.article")

    if len(articles) != 1:
        raise ArticleNotFound()

    article = articles[0]
    article.attrs = {}

    buzz_blocks = [
        *article.select('.article-disclaimer'),
        *article.select('footer.article-footer'),
        *article.select('aside'),
    ]
    for el in buzz_blocks:
        el.decompose()

    remove_buzz_attrs(article)
    remove_buzz_tags(article)

    if not plaintext:
        article_text = article.prettify()
    else:
        remove_all_tags(article)
        article_text = article.get_text()

    return article_text.strip()
