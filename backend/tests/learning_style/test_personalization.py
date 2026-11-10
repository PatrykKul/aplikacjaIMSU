from app.modules.learning_style.personalization import (
    collapsed_ids,
    effective_style,
    matches_style,
    style_explanation,
)

TEXT = {"id": "t", "type": "text"}


def attachment(block_id: str, forms: list[str]) -> dict:
    return {"id": block_id, "type": "attachment", "forms": forms}


def test_text_is_common():
    assert matches_style(TEXT, "V")
    assert matches_style(TEXT, "K")


def test_attachment_needs_a_shared_form():
    assert matches_style(attachment("a", ["V"]), "V")
    assert not matches_style(attachment("a", ["V"]), "A")
    assert matches_style(attachment("a", ["V", "A"]), "A")
    assert matches_style(attachment("a", ["V", "A", "K"]), "K")


def test_mixed_style_matches_both_styles():
    assert matches_style(attachment("a", ["V"]), "VA")
    assert matches_style(attachment("a", ["A"]), "VA")
    assert not matches_style(attachment("a", ["K"]), "VA")


def test_collapsed_ids_keep_the_teachers_order():
    blocks = [attachment("k", ["K"]), TEXT, attachment("v", ["V"]), attachment("a", ["A"])]
    assert collapsed_ids(blocks, "V") == ["k", "a"]
    assert collapsed_ids(blocks, "VAK") == []


def test_effective_style_adds_opened_forms_in_vak_order():
    assert effective_style("V", []) == "V"
    assert effective_style("V", ["A"]) == "VA"
    assert effective_style("K", ["A", "VA"]) == "VAK"
    assert effective_style("VA", ["A"]) == "VA"
    assert effective_style("", ["K", "V"]) == "VK"


def test_explanations():
    survey = style_explanation("V", "survey", {"V": 12, "A": 5, "K": 3})
    assert "wzrokowiec" in survey and "V 12 / A 5 / K 3" in survey
    assert "ręcznie" in style_explanation("A", "manual", None)
    assert "quizów" in style_explanation("K", "adaptation", None)
