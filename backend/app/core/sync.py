"""Helpers for synchronising database rows with definitions loaded from files."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Changes:
    """What one synchronization did to one kind of element."""

    created: int = 0
    updated: int = 0
    archived: int = 0
    removed: int = 0

    @property
    def total(self) -> int:
        return self.created + self.updated + self.archived + self.removed


def assign_changed(obj: Any, **values: Any) -> bool:
    """Set only the attributes whose value differs; return True if anything changed."""
    changed = False
    for key, value in values.items():
        if getattr(obj, key) != value:
            setattr(obj, key, value)
            changed = True
    return changed
