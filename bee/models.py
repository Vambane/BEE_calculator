"""Input and result data models for the scoring engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class EnterpriseSize(StrEnum):
    EME = "EME"
    QSE = "QSE"
    GENERIC = "Generic"


class YesTier(StrEnum):
    """YES Initiative recognition tiers (S6 cl. 5.1)."""

    NONE = "none"
    TARGET = "target"  # target met + 2.5% absorption -> +1 level
    TARGET_1_5X = "1.5x"  # 1.5x target + 5% absorption -> +1 level and +3 points
    TARGET_2X = "2x"  # 2x target + 5% absorption -> +2 levels


@dataclass(frozen=True)
class Rand:
    """A raw rand amount (or headcount). The engine converts it to a percentage of the
    indicator's base (NPAT, leviable amount, TMPS, headcount) from ``Financials``."""

    amount: float


@dataclass(frozen=True)
class Financials:
    """Bases used to derive percentages from raw rand amounts."""

    npat: float | None = None
    leviable_amount: float | None = None
    tmps: float | None = None  # total measured procurement spend
    employees: float | None = None


@dataclass(frozen=True)
class CompanyProfile:
    total_revenue: float
    black_ownership_pct: float = 0.0
    sector: str = "generic"
    variant: str | None = None  # sector sub-scorecard, e.g. "contractor", "bank"
    opt_scored: bool = False  # black-owned QSE / EME electing to be scored (S5 cl. 4.5, 5.4)


@dataclass(frozen=True)
class YesInput:
    tier: YesTier = YesTier.NONE
    previous_level: int | None = None  # 1..8; 9 = non-compliant. Used for the S6 cl. 2.4 test.


IndicatorValue = float | bool | Rand


@dataclass
class ScoreInput:
    """Either give raw indicator values per element (``indicators``) or pre-computed
    points per sub-element group (``points``). ``points`` wins where both are given.

    ``indicators``: {element: {clause: value}}; value is a percentage (float), a Rand
    amount, or a bool for yes/no bonuses.
    ``points``: {element: {group: points}}, e.g. {"esd": {"pp": 20, "sd": 8, "ed": 4}}.
    """

    profile: CompanyProfile
    financials: Financials = field(default_factory=Financials)
    indicators: dict[str, dict[str, IndicatorValue]] = field(default_factory=dict)
    points: dict[str, dict[str, float]] = field(default_factory=dict)
    yes: YesInput = field(default_factory=YesInput)
    draft_rules: bool = False  # D4: 2026 draft / Transformation Fund, OFF by default
    # Sector options, e.g. {"fs_skills_submin": 6, "fs_rescale_109": True,
    # "eme_skills_pct_of_qse_target": 30, "start_up": False}. See bee/sectors.
    options: dict[str, object] = field(default_factory=dict)


@dataclass
class SubMinimumCheck:
    element: str
    group: str | None
    achieved: float
    required: float
    clause: str
    option_used: str | None = None

    @property
    def passed(self) -> bool:
        return self.achieved >= self.required - 1e-9


@dataclass
class ScoreResult:
    size: EnterpriseSize
    level: int  # 1..8, 9 = non-compliant
    recognition_pct: int
    total_points: float | None = None
    element_points: dict[str, float] = field(default_factory=dict)
    group_points: dict[str, dict[str, float]] = field(default_factory=dict)
    deemed: bool = False
    level_before_discount: int | None = None
    discounted: bool = False
    submin_checks: list[SubMinimumCheck] = field(default_factory=list)
    yes_applied: bool = False
    yes_blocked_reason: str | None = None
    notes: list[str] = field(default_factory=list)
    sector: str = "generic"
    variant: str | None = None
    scorecard: str | None = None
    warnings: list[str] = field(default_factory=list)
    level_points: float | None = None  # points used for the level table (after rescaling)

    @property
    def level_label(self) -> str:
        return "Non-compliant" if self.level == 9 else f"Level {self.level}"
