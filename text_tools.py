import string
import re


def has_latin_letters(string):
    characherregex = re.compile(r'[a-zA-Z]')
    return any(characherregex.search(symbol) for symbol in string)


def _clean_word(word):
    word = word.replace('«', '').replace('»', '').replace('…', '')
    word = word.replace('"', '').replace('"', '').replace('_', '')
    word = word.replace(':', '').replace('.', '').replace(',', '')
    word = word.strip(string.punctuation)
    if not word.isdigit():
        return word


def split_by_words(morph, text):
    """Учитывает знаки пунктуации, регистр и словоформы, выкидывает предлоги."""
    words = []
    for word in text.split():
        cleaned_word = _clean_word(word)
        if cleaned_word:
            normalized_word = morph.parse(cleaned_word)[0].normal_form
            if len(normalized_word) > 2 or normalized_word == 'не':
                words.append(normalized_word)
    splitted = [word for word in words if not has_latin_letters(word)]
    return [word for word in splitted if word]


def calculate_jaundice_rate(article_words, charged_words):
    """Расчитывает желтушность текста,
    принимает список "заряженных" слов и ищет их внутри article_words."""

    if not article_words:
        return 0.0

    found_charged_words = [word for word in article_words if
                           word in set(charged_words)]
    score = len(found_charged_words) / len(article_words) * 100
    return round(score, 2)


