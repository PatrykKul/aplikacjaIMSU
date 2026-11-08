from app.modules.learning_style.personalization import (
    block_visible,
    personalize,
    style_explanation,
)

TEXT = {"id": "t", "type": "text"}


def attachment(block_id: str, forms: list[str]) -> dict:
    return {"id": block_id, "type": "attachment", "forms": forms}


def test_text_is_common():
    assert block_visible(TEXT, "V")
    assert block_visible(TEXT, "K")


def test_attachment_needs_a_shared_form():
    assert block_visible(attachment("a", ["V"]), "V")
    assert not block_visible(attachment("a", ["V"]), "A")
    assert block_visible(attachment("a", ["V", "A"]), "A")
    assert block_visible(attachment("a", ["V", "A", "K"]), "K")


def test_mixed_style_sees_both_styles():
    assert block_visible(attachment("a", ["V"]), "VA")
    assert block_visible(attachment("a", ["A"]), "VA")
    assert not block_visible(attachment("a", ["K"]), "VA")


def test_personalize_keeps_order_and_counts_hidden():
    blocks = [attachment("k", ["K"]), TEXT, attachment("v", ["V"]), attachment("a", ["A"])]
    visible, hidden = personalize(blocks, "V")
    assert [b["id"] for b in visible] == ["t", "v"]
    assert hidden == 2


def test_explanations():
    survey = style_explanation("V", "survey", {"V": 12, "A": 5, "K": 3})
    assert "wzrokowiec" in survey and "V 12 / A 5 / K 3" in survey
    assert "ręcznie" in style_explanation("A", "manual", None)
    assert "quizów" in style_explanation("K", "adaptation", None)
