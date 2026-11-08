from app.modules.learning_style.adaptation import (
    counts_for_weights,
    initial_weights,
    is_passed,
    proposal_message,
    proposal_why,
    proposed_style,
    quiz_why,
    ranking,
    update_weights,
)


def test_pass_threshold():
    assert is_passed(70)
    assert not is_passed(69)


def test_initial_weights_are_survey_points_clamped():
    assert initial_weights({"V": 12, "A": 5, "K": 3}) == {"V": 12, "A": 5, "K": 3}
    assert initial_weights({"V": 40, "A": -2}) == {"V": 30, "A": 0, "K": 0}


def test_update_weights_for_each_letter_of_the_style():
    weights = {"V": 5, "A": 5, "K": 5}
    assert update_weights(weights, "V", True) == {"V": 6, "A": 5, "K": 5}
    assert update_weights(weights, "VA", False) == {"V": 4, "A": 4, "K": 5}


def test_update_weights_stays_in_range():
    assert update_weights({"V": 30, "A": 0, "K": 1}, "VA", True)["V"] == 30
    assert update_weights({"V": 30, "A": 0, "K": 1}, "VA", False)["A"] == 0


def test_only_first_success_and_first_failure_count():
    assert counts_for_weights([], True)
    assert counts_for_weights([False], True)
    assert not counts_for_weights([True], True)
    assert not counts_for_weights([True, False], False)


def test_ranking_breaks_ties_in_vak_order():
    assert ranking({"V": 3, "A": 5, "K": 5}) == ["A", "K", "V"]


def test_proposal_for_a_sole_leader_outside_the_style():
    assert proposed_style({"V": 6, "A": 9, "K": 2}, "V", "survey", None) == "A"


def test_no_proposal_on_tie_or_when_leader_is_in_style():
    assert proposed_style({"V": 9, "A": 9, "K": 2}, "K", "survey", None) is None
    assert proposed_style({"V": 6, "A": 9, "K": 2}, "VA", "survey", None) is None


def test_manual_style_and_rejected_proposal_are_respected():
    weights = {"V": 6, "A": 9, "K": 2}
    assert proposed_style(weights, "V", "manual", None) is None
    assert proposed_style(weights, "V", "survey", "A") is None
    assert proposed_style(weights, "V", "adaptation", None) == "A"


def test_texts():
    assert proposal_message("A") == "Lepiej Ci idzie z materiałami słuchowymi – przełączyć?"
    assert "V 6 / A 9 / K 2" in proposal_why({"V": 6, "A": 9, "K": 2}, "A")
    assert "45%" in quiz_why("Wykres", 45) and "poniżej progu" in quiz_why("Wykres", 45)
    assert "zaliczony" in quiz_why("Wykres", 80)
