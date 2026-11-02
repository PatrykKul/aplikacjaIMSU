from fractions import Fraction

import pytest

from app.modules.content.numbers import parse_number


@pytest.mark.parametrize(
    ("text", "unit", "expected"),
    [
        ("25", None, Fraction(25)),
        ("25,5", None, Fraction(51, 2)),
        ("25.5", None, Fraction(51, 2)),
        (" 25 % ", None, Fraction(25)),
        ("30 zł", "zł", Fraction(30)),
        ("30zł", "zł", Fraction(30)),
        ("1/4", None, Fraction(1, 4)),
        ("0,25", None, Fraction(1, 4)),
        ("-3", None, Fraction(-3)),
        ("\u22123", None, Fraction(-3)),
        ("1 000", None, Fraction(1000)),
        ("1\u00a0000", None, Fraction(1000)),
    ],
)
def test_parse_number(text, unit, expected):
    assert parse_number(text, unit=unit) == expected


@pytest.mark.parametrize("text", ["", "   ", "abc", "1/0", "2,5,1", "30 zł", "1/2/3", "--3", ".5"])
def test_parse_number_rejects(text):
    with pytest.raises(ValueError):
        parse_number(text)
