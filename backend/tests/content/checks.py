"""Independent calculations for `check` data in course lesson files.

A number question in a lesson can carry `check: {op: <name>, ...arguments}`. Content tests
recalculate the answer with the operation below (exact fractions, no floats) and compare it
with the `value` written by the author. A new course that needs a new kind of calculation
adds one operation here.
"""

from collections.abc import Callable
from fractions import Fraction
from typing import Any

from app.modules.content.numbers import parse_number


def number(value: Any) -> Fraction:
    return parse_number(str(value))


def _change(n: Any, p: Any) -> Fraction:
    return number(n) * (1 + number(p) / 100)


def _successive(n: Any, ps: list[Any]) -> Fraction:
    result = number(n)
    for p in ps:
        result = _change(result, p)
    return result


OPERATIONS: dict[str, Callable[..., Fraction]] = {
    # --- percentages ---
    # p% of n
    "percent_of": lambda p, n: number(p) * number(n) / 100,
    # what percent of `whole` is `part`
    "ratio_percent": lambda part, whole: number(part) / number(whole) * 100,
    # the whole number whose p% equals `part`
    "whole_from_part": lambda p, part: number(part) * 100 / number(p),
    # p% written as a fraction or decimal
    "to_decimal": lambda p: number(p) / 100,
    # fraction or decimal x written in percent
    "to_percent": lambda x: number(x) * 100,
    # n after a change by p% (p < 0 for a decrease)
    "change": _change,
    # by how many percent a value changed; the direction is given by the question
    "change_percent": lambda old, new: abs(number(new) - number(old)) / number(old) * 100,
    # n after several changes by p% in a row
    "successive": _successive,
    # percent left after taking away the listed parts of a whole (100% - sum)
    "rest_percent": lambda parts: 100 - sum(number(part) for part in parts),
    # --- fractions ---
    # fraction x of n, e.g. 1/4 of 36
    "fraction_of": lambda x, n: number(x) * number(n),
}


def evaluate(check: dict[str, Any]) -> Fraction:
    """Result of a `check` entry; KeyError for an unknown operation."""
    arguments = dict(check)
    operation = OPERATIONS[arguments.pop("op")]
    return operation(**arguments)
