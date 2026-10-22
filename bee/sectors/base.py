from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from bee.models import EnterpriseSize
from bee.rules import Element, Scorecard, SubMinimum

Status = Literal["verified", "unverified", "excluded", "not_loaded", "legacy"]


class SectorExcludedError(ValueError):
    """Raised when a sector is deliberately not supported (e.g. MAC)."""


@dataclass(frozen=True)
class Thresholds:
    eme_max: float  # EME if revenue <= eme_max (or < if not eme_inclusive)
    large_min: float  # Large if revenue >= large_min (or > if not large_inclusive)
    eme_inclusive: bool = True
    large_inclusive: bool = True

    def classify(self, revenue: float) -> EnterpriseSize:
        if revenue < 0:
            raise ValueError("total_revenue must be >= 0")
        if revenue < self.eme_max or (self.eme_inclusive and revenue == self.eme_max):
            return EnterpriseSize.EME
        if revenue > self.large_min or (self.large_inclusive and revenue == self.large_min):
            return EnterpriseSize.GENERIC
        return EnterpriseSize.QSE


GENERIC_THRESHOLDS = Thresholds(10_000_000, 50_000_000)
# (minimum black ownership %, deemed level), checked in order.
GENERIC_EME_DEEMED: tuple[tuple[float, int], ...] = ((100, 1), (51, 2), (0, 4))


@dataclass(frozen=True)
class SectorConfig:
    key: str
    name: str
    gazette: str
    status: Status
    cards: dict[tuple[EnterpriseSize, str | None], Scorecard]
    thresholds: dict[str | None, Thresholds] = field(
        default_factory=lambda: {None: GENERIC_THRESHOLDS}
    )
    eme_deemed: tuple[tuple[float, int], ...] = GENERIC_EME_DEEMED
    qse_deemed: bool = True  # >=51% black-owned QSE deemed L2, 100% L1
    variants: tuple[str, ...] = ()
    default_variant: str | None = None
    warnings: tuple[str, ...] = ()
    size_labels: dict[EnterpriseSize, str] = field(default_factory=dict)
    construction_eme_rules: bool = False  # Construction cl. 4.3, 3.6.2.4

    def resolve_variant(self, variant: str | None) -> str | None:
        v = variant if variant is not None else self.default_variant
        if self.variants and v not in self.variants:
            raise KeyError(f"{self.key}: variant must be one of {self.variants}, got {v!r}")
        return v if self.variants else None

    def threshold(self, variant: str | None) -> Thresholds:
        return self.thresholds.get(variant, self.thresholds.get(None, GENERIC_THRESHOLDS))

    def card(self, size: EnterpriseSize, variant: str | None) -> Scorecard:
        if size == EnterpriseSize.EME:
            size = EnterpriseSize.QSE  # EMEs opting to be scored use the QSE scorecard
        for key in ((size, variant), (size, None)):
            if key in self.cards:
                return self.cards[key]
        raise KeyError(f"{self.key}: no scorecard for size={size} variant={variant!r}")

    def deemed_eme_level(self, black_ownership_pct: float) -> int:
        for minimum, level in self.eme_deemed:
            if black_ownership_pct >= minimum:
                return level
        return self.eme_deemed[-1][1]


def el(
    key: str,
    name: str,
    total: float,
    priority: bool = False,
    groups: dict[str, float] | None = None,
    bonus: float = 0.0,
) -> Element:
    """Element-level config (no indicator table): points input only."""
    return Element(
        key,
        name,
        (),
        priority=priority,
        total=total,
        group_max=tuple((groups or {}).items()),
        bonus_max=bonus,
    )


def sm(element: str, group: str | None, required: float, clause: str, **kw) -> SubMinimum:
    return SubMinimum(element, group, required, clause, **kw)
