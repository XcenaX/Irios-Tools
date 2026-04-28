from __future__ import annotations

import re
from functools import lru_cache

import pymorphy3


WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё-]+|[^A-Za-zА-Яа-яЁё-]+")
CYRILLIC_RE = re.compile(r"^[А-Яа-яЁё-]+$")
NOUN_LIKE_POS = {"NOUN", "ADJF", "PRTF"}
NAME_GRAMS = ("Surn", "Name", "Patr")

_MORPH = pymorphy3.MorphAnalyzer()


def _restore_case(source: str, target: str) -> str:
    if source.isupper():
        return target.upper()
    if source.istitle():
        return target[:1].upper() + target[1:]
    return target


@lru_cache(maxsize=2048)
def _best_parse(word: str) -> pymorphy3.analyzer.Parse | None:
    parses = _MORPH.parse(word)
    return parses[0] if parses else None


def _inflect_word(word: str, target_case: str, *, prefer_names: bool = False, only_nominative_like: bool = False) -> str:
    if not CYRILLIC_RE.fullmatch(word) or word.isupper():
        return word

    if "-" in word:
        return "-".join(
            _inflect_word(part, target_case, prefer_names=prefer_names, only_nominative_like=only_nominative_like)
            for part in word.split("-")
        )

    parses = _MORPH.parse(word)
    if not parses:
        return word

    if prefer_names:
        parses.sort(key=lambda item: tuple(gram in item.tag for gram in NAME_GRAMS), reverse=True)

    parse = parses[0]
    if only_nominative_like and parse.tag.case not in {"nomn", None}:
        return word
    if parse.tag.POS not in NOUN_LIKE_POS and not prefer_names:
        return word

    inflected = parse.inflect({target_case})
    if inflected is None:
        return word
    return _restore_case(word, inflected.word)


def decline_full_name(full_name: str, target_case: str = "accs") -> str:
    parts = [part for part in str(full_name).split() if part]
    return " ".join(_inflect_word(part, target_case, prefer_names=True) for part in parts)


def decline_position(position: str, target_case: str = "accs") -> str:
    chunks = WORD_RE.findall(str(position))
    return "".join(_inflect_word(chunk, target_case, only_nominative_like=True) if CYRILLIC_RE.fullmatch(chunk) else chunk for chunk in chunks)


def probation_phrase_with_words(value: str | int | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.search(r"\d+", text)
    if not match:
        return text
    number = int(match.group(0))
    words = {
        1: "один",
        2: "два",
        3: "три",
        4: "четыре",
        5: "пять",
        6: "шесть",
        7: "семь",
        8: "восемь",
        9: "девять",
        10: "десять",
        11: "одиннадцать",
        12: "двенадцать",
    }.get(number)
    month_form = "месяц" if number % 10 == 1 and number % 100 != 11 else "месяца" if number % 10 in {2, 3, 4} and number % 100 not in {12, 13, 14} else "месяцев"
    if words:
        return f"{number} ({words}) {month_form}"
    return f"{number} {month_form}"
