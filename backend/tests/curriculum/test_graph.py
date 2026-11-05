from app.modules.curriculum.graph import find_cycle


def test_empty_graph_has_no_cycle():
    assert find_cycle({}) is None


def test_percentages_graph_has_no_cycle():
    requires = {
        "percent-as-fraction": [],
        "percent-of-number": ["percent-as-fraction"],
        "percent-ratio": ["percent-as-fraction"],
        "number-from-percent": ["percent-of-number"],
        "percent-change": ["percent-of-number", "percent-ratio"],
        "successive-changes": ["percent-change"],
    }
    assert find_cycle(requires) is None


def test_prerequisite_missing_from_keys_is_treated_as_leaf():
    assert find_cycle({"a": ["b"]}) is None


def test_self_loop():
    assert find_cycle({"a": ["a"]}) == ["a", "a"]


def test_two_node_cycle():
    assert find_cycle({"a": ["b"], "b": ["a"]}) == ["a", "b", "a"]


def test_three_node_cycle_reached_from_outside():
    requires = {"x": ["a"], "a": ["b"], "b": ["c"], "c": ["a"]}
    assert find_cycle(requires) == ["a", "b", "c", "a"]


def test_cycle_in_second_component():
    requires = {"a": ["b"], "b": [], "p": ["q"], "q": ["p"]}
    assert find_cycle(requires) == ["p", "q", "p"]
