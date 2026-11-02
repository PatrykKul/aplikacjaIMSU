"""Exact parsing of numbers typed by students and written in course files (no floats)."""

import re
from fractions import Fraction

_SPACES = re.compile(r"[\s\u00a0\u202f]+")
_DECIMAL = re.compile(r"^[+-]?\d+(\.\d+)?$")
_FRACTION = re.compile(r"^([+-]?\d+)/(\d+)$")


def parse_number(text: str, unit: str | None = None) -> Fraction:
    """Read '25', '25,5', ' 25 % ', '30 zł' (unit='zł'), '1/4', '-3' as an exact Fraction.

    Spaces are ignored (also '1 000'), a decimal comma is accepted, and a trailing
    unit or '%' sign is dropped. Raises ValueError for anything else.
    """
    cleaned = _SPACES.sub("", text).replace(",", ".").replace("\u2212", "-")
    if unit:
        cleaned = cleaned.removesuffix(_SPACES.sub("", unit))
    cleaned = cleaned.removesuffix("%")

    if match := _FRACTION.match(cleaned):
        numerator, denominator = int(match[1]), int(match[2])
        if denominator == 0:
            raise ValueError(f"zero denominator: {text!r}")
        return Fraction(numerator, denominator)
    if _DECIMAL.match(cleaned):
        return Fraction(cleaned)
    raise ValueError(f"not a number: {text!r}")
