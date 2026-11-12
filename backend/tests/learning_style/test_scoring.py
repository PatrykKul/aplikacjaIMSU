import pytest

from app.modules.learning_style.scoring import (
    compute_score,
    dominant_styles,
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
