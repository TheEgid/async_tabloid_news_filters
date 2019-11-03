from . import inosmi_ru
from .exceptions import ArticleNotFound, HeaderNotFound

__all__ = ['SANITIZERS', 'ArticleNotFound', 'HeaderNotFound']

SANITIZERS = {
    'inosmi_ru': [
        inosmi_ru.sanitize_article_text,
        inosmi_ru.sanitize_article_header,
        inosmi_ru.ArticleNotFound,
        inosmi_ru.HeaderNotFound,
    ]
}
