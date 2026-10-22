"""Input/result data models. Stub: fields are added in the engine milestone."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EnterpriseSize(StrEnum):
    EME = "EME"
    QSE = "QSE"
    GENERIC = "Generic"


@dataclass(frozen=True)
class CompanyProfile:
    total_revenue: float
    black_ownership_pct: float = 0.0


@dataclass
class ScoreResult:
    size: EnterpriseSize
    level: str
    total_points: float = 0.0
    element_points: dict[str, float] = field(default_factory=dict)
    discounted: bool = False
