"""Net Value points per Statement 100, Annexe 100(E) (Amended Codes, GG 36928 / GG 42496).

Net Value is the lower of two results, each capped at the indicator weighting W
(8 points on the Generic card):

Formula A (time-based graduation, debt-adjusted)::

    deemed value  = (B - C) / D
    points_A      = deemed value / (T x F) x W

    B  value of the equity instruments held by black participants
    C  carrying value of their acquisition debt (outstanding balance)
    D  value of the measured entity
    T  Net Value target (25% on the Generic card)
    F  time-based graduation factor for the year since the current equity interest date

Formula B (economic interest)::

    points_B      = E / T x W

    E  % economic interest held by black participants

Values are taken on the measurement date. For an unlisted entity, B and D come from a
competent person's valuation; a listed entity may use the market price where the shares
carry no extra restrictions. Flow-through, modified flow-through and the 2019
"current equity interest date" rules are inputs here, not calculated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

DEFAULT_TARGET = 25.0  # % (Statement 100 cl. 2.3.1 / Annexe 100(C))

# Annexe 100(E) para 4: graduation factor by year since the current equity interest date.
GRADUATION: dict[int, float] = {
    1: 0.10,
    2: 0.20,
    3: 0.40,
    4: 0.40,
    5: 0.60,
    6: 0.60,
    7: 0.80,
    8: 0.80,
    9: 1.00,
    10: 1.00,
}
MAX_YEAR = max(GRADUATION)


def graduation_factor(year: int) -> float:
    """Factor F for ``year`` (1 = first 12 months). Year 10 onwards is 100%."""
    if year < 1:
        raise ValueError("Year must be 1 or later.")
    return GRADUATION[min(year, MAX_YEAR)]


def measurement_year(equity_date: date, measurement_date: date) -> int:
    """Year number since the current equity interest date (year 1 = first 12 months).

    The day of the equity date starts year 1; each anniversary starts the next year.
    """
    if measurement_date < equity_date:
        raise ValueError("The measurement date is before the current equity interest date.")
    years = measurement_date.year - equity_date.year
    if (measurement_date.month, measurement_date.day) < (equity_date.month, equity_date.day):
        years -= 1
    return years + 1


@dataclass(frozen=True)
class NetValueInput:
    """All rand figures on the measurement date. Percentages are 0 to 100."""

    black_equity_value: float  # B
    acquisition_debt: float  # C
    entity_value: float  # D
    economic_interest_pct: float  # E
    year: int  # years since the current equity interest date (1-based)
    weighting: float = 8.0  # W, from the scorecard
    target_pct: float = DEFAULT_TARGET  # T


@dataclass(frozen=True)
class NetValueResult:
    deemed_value_pct: float  # (B - C) / D, floored at 0, as %
    required_pct: float  # T x F, as %
    graduation: float  # F
    points_a: float
    points_b: float
    points: float  # min(points_a, points_b)
    binding: str  # "A", "B" or "A and B"
    weighting: float  # W
    notes: list[str] = field(default_factory=list)

    @property
    def pct_of_target(self) -> float:
        """Engine input: % of the Net Value weighting achieved (0 to 100)."""
        return self.points / self.weighting * 100


def validate(inp: NetValueInput) -> list[str]:
    """Every problem with the inputs at once (empty list when valid)."""
    errs: list[str] = []
    if inp.entity_value <= 0:
        errs.append("Value of the measured entity must be more than zero.")
    if inp.black_equity_value < 0:
        errs.append("Value of black-held equity cannot be negative.")
    if inp.acquisition_debt < 0:
        errs.append("Acquisition debt cannot be negative.")
    if inp.entity_value > 0 and inp.black_equity_value > inp.entity_value:
        errs.append("Black-held equity cannot be worth more than the whole entity.")
    if not 0 <= inp.economic_interest_pct <= 100:
        errs.append("Economic interest must be between 0% and 100%.")
    if inp.year < 1:
        errs.append("Year must be 1 or later.")
    if inp.weighting <= 0:
        errs.append("Net Value weighting must be more than zero.")
    if not 0 < inp.target_pct <= 100:
        errs.append("Net Value target must be between 0% and 100%.")
    return errs


def calculate(inp: NetValueInput) -> NetValueResult:
    """Net Value points for ``inp``. Raises ValueError listing every input problem."""
    errs = validate(inp)
    if errs:
        raise ValueError("; ".join(errs))
    w, t = inp.weighting, inp.target_pct / 100
    f = graduation_factor(inp.year)
    notes: list[str] = []

    net = inp.black_equity_value - inp.acquisition_debt
    if net < 0:
        notes.append(
            "Acquisition debt is more than the value of the black-held equity, so the deemed "
            "value is nil and Formula A scores 0."
        )
    deemed = max(net, 0.0) / inp.entity_value
    raw_a = deemed / (t * f) * w
    raw_b = inp.economic_interest_pct / 100 / t * w
    pa, pb = min(raw_a, w), min(raw_b, w)
    if raw_a > w:
        notes.append(f"Formula A gave {raw_a:.2f}, capped at {w:g}.")
    if raw_b > w:
        notes.append(f"Formula B gave {raw_b:.2f}, capped at {w:g}.")
    if abs(pa - pb) < 1e-9:
        binding = "A and B"
    else:
        binding = "A" if pa < pb else "B"
    if deemed * 100 > inp.economic_interest_pct + 1e-9:
        notes.append(
            "The deemed value is higher than the economic interest entered. Check that both "
            "measure the same black shareholding."
        )
    return NetValueResult(
        deemed_value_pct=deemed * 100,
        required_pct=t * f * 100,
        graduation=f,
        points_a=pa,
        points_b=pb,
        points=min(pa, pb),
        binding=binding,
        weighting=w,
        notes=notes,
    )
