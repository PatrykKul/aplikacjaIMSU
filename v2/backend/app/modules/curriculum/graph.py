"""Pure functions on the skill prerequisite graph (no database, no framework)."""

from collections.abc import Iterable, Mapping

_UNVISITED, _IN_PROGRESS, _DONE = 0, 1, 2


def find_cycle(requires: Mapping[str, Iterable[str]]) -> list[str] | None:
    """Return one cycle as a path with the first node repeated at the end, or None.

    `requires[a]` lists the skills that `a` requires.
    """
    graph = {node: list(prerequisites) for node, prerequisites in requires.items()}
    state: dict[str, int] = {}
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        state[node] = _IN_PROGRESS
        path.append(node)
        for prerequisite in graph.get(node, ()):
            prerequisite_state = state.get(prerequisite, _UNVISITED)
            if prerequisite_state == _IN_PROGRESS:
                return path[path.index(prerequisite) :] + [prerequisite]
            if prerequisite_state == _UNVISITED:
                cycle = visit(prerequisite)
                if cycle:
                    return cycle
        path.pop()
        state[node] = _DONE
        return None

    # Sorted start nodes: the same graph always reports the same cycle
    for node in sorted(graph):
        if state.get(node, _UNVISITED) == _UNVISITED:
            cycle = visit(node)
            if cycle:
                return cycle
    return None
