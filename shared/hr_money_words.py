from __future__ import annotations


UNITS = {
    "male": [
        "ноль",
        "один",
        "два",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    ],
    "female": [
        "ноль",
        "одна",
        "две",
        "три",
        "четыре",
        "пять",
        "шесть",
        "семь",
        "восемь",
        "девять",
    ],
}

TEENS = [
    "десять",
    "одиннадцать",
    "двенадцать",
    "тринадцать",
    "четырнадцать",
    "пятнадцать",
    "шестнадцать",
    "семнадцать",
    "восемнадцать",
    "девятнадцать",
]

TENS = [
    "",
    "",
    "двадцать",
    "тридцать",
    "сорок",
    "пятьдесят",
    "шестьдесят",
    "семьдесят",
    "восемьдесят",
    "девяносто",
]

HUNDREDS = [
    "",
    "сто",
    "двести",
    "триста",
    "четыреста",
    "пятьсот",
    "шестьсот",
    "семьсот",
    "восемьсот",
    "девятьсот",
]

SCALES = [
    ("", "", "", "male"),
    ("тысяча", "тысячи", "тысяч", "female"),
    ("миллион", "миллиона", "миллионов", "male"),
    ("миллиард", "миллиарда", "миллиардов", "male"),
]


def _plural_form(number: int, form1: str, form2: str, form5: str) -> str:
    number = abs(number) % 100
    if 11 <= number <= 19:
        return form5
    tail = number % 10
    if tail == 1:
        return form1
    if 2 <= tail <= 4:
        return form2
    return form5


def _triplet_to_words(number: int, gender: str) -> list[str]:
    if number == 0:
        return []

    words: list[str] = []
    hundreds = number // 100
    tens_units = number % 100
    tens = tens_units // 10
    units = tens_units % 10

    if hundreds:
        words.append(HUNDREDS[hundreds])

    if 10 <= tens_units <= 19:
        words.append(TEENS[tens_units - 10])
        return words

    if tens:
        words.append(TENS[tens])
    if units:
        words.append(UNITS[gender][units])
    return words


def number_to_russian_words(value: int) -> str:
    if value == 0:
        return "ноль"
    if value < 0:
        return f"минус {number_to_russian_words(abs(value))}"

    parts: list[str] = []
    scale_index = 0
    while value > 0:
        triplet = value % 1000
        if triplet:
            one, two, five, gender = SCALES[scale_index]
            words = _triplet_to_words(triplet, gender)
            if scale_index > 0:
                words.append(_plural_form(triplet, one, two, five))
            parts.insert(0, " ".join(words))
        value //= 1000
        scale_index += 1
    return " ".join(part for part in parts if part).strip()


def salary_to_tenge_words(value: str | int | float | None) -> str:
    if value in (None, ""):
        return ""
    try:
        amount = int(float(str(value).replace(" ", "").replace(",", ".")))
    except ValueError:
        return str(value)
    return number_to_russian_words(amount)
