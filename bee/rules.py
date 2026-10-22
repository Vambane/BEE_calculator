"""Rule config types. Scorecards are pure data so sector codes can be added as data files."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Base = Literal["pct", "npat", "leviable", "tmps", "employees", "bool"]


@dataclass(frozen=True)
class Indicator:
    clause: str
    name: str
    points: float
    target: float  # percent of base (ignored for bool)
    base: Base = "pct"
    group: str = "main"
    bonus: bool = False
    draft_only: bool = False
    draft_points: float | None = None  # weighting under the 2026 draft, if it changes


@dataclass(frozen=True)
class Element:
    key: str
    name: str
    indicators: tuple[Indicator, ...]
    priority: bool = False

    def max_points(self, group: str | None = None, draft: bool = False) -> float:
        return sum(
            i.points
            for i in self.indicators
            if not i.bonus and (group is None or i.group == group) and (draft or not i.draft_only)
        )

    def groups(self) -> list[str]:
        return list(dict.fromkeys(i.group for i in self.indicators))


@dataclass(frozen=True)
class SubMinimum:
    element: str
    group: str | None  # None = whole element (bonus excluded)
    required: float
    clause: str
    draft_only: bool = False
    replaced_by_draft: bool = False  # e.g. SD/ED tests replaced by TF test on TF route


@dataclass(frozen=True)
class Scorecard:
    key: str
    name: str
    elements: tuple[Element, ...]
    submins: tuple[SubMinimum, ...]
    # "all": every sub-minimum must pass (Generic, S5 cl. 3.3.2.1).
    # "ownership_plus_one": Ownership + (Skills or ESD) (QSE, S5 cl. 3.3.2.2).
    priority_rule: Literal["all", "ownership_plus_one"] = "all"
    sources: tuple[str, ...] = field(default_factory=tuple)

    def element(self, key: str) -> Element:
        for e in self.elements:
            if e.key == key:
                return e
        raise KeyError(key)
