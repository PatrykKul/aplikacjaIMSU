import pytest

from app.modules.learning_style.scoring import (
    compute_score,
    describe_style,
    dominant_styles,
    is_valid_style,
)


def test_each_answer_gives_one_point():
    score = compute_score(["V", "V", "A", "K", "V"])
    assert score.points == {"V": 3, "A": 1, "K": 1}
    assert score.dominant_style == "V"


def test_tie_gives_mixed_style_in_vak_order():
    assert compute_score(["A", "V"]).dominant_style == "VA"
    assert compute_score(["K", "A", "V"]).dominant_style == "VAK"
    assert dominant_styles({"V": 2, "A": 5, "K": 5}) == "AK"


def test_no_answers_is_an_error():
    with pytest.raises(ValueError):
        compute_score([])


def test_unknown_style_is_an_error():
    with pytest.raises(ValueError):
        compute_score(["V", "X"])


@pytest.mark.parametrize("style", ["V", "A", "K", "VA", "VK", "AK", "VAK"])
def test_valid_styles(style: str):
    assert is_valid_style(style)


@pytest.mark.parametrize("style", [None, "", "AV", "VV", "X", "va", "VAKV"])
def test_invalid_styles(style: str | None):
    assert not is_valid_style(style)


def test_describe_style():
    assert describe_style("VA") == "wzrokowiec + słuchowiec"
    assert describe_style("K") == "kinestetyk"
