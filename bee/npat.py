"""NPAT basis for the NPAT-linked targets (Supplier Development, Enterprise Development, SED,
and the draft Transformation Fund): Statement 400 cl. 3.2.1, GG 42496.

The NPAT target applies unless (cl. 3.2.1.1-3.2.1.2):
- the entity made no profit last year, or none on average over the last five years; or
- its net profit margin is below a quarter of the industry norm.

Then the target is set on Turnover (cl. 3.2.1.3.1): rate x Indicative Profit Margin
(NPAT / Turnover) x Turnover. That is the same as scoring against a *deemed NPAT* of
Indicative Profit Margin x Turnover, which is how the engine applies it: every NPAT-based
indicator divides by the deemed figure.

The Indicative Profit Margin is taken from the most recent year in which the margin was at
least a quarter of the industry norm (B-BBEE Commission FAQ). Where no such year exists the
app falls back to a quarter of the industry norm: an INTERPRETATION, flagged in results.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class NpatBasis:
    npat: float | None  # the base NPAT-linked targets are scored against
    deemed: bool = False
    reasons: tuple[str, ...] = ()
    margin_pct: float | None = None  # Indicative Profit Margin used (deemed only)
    interpretation: bool = False  # True when the quarter-of-norm fallback was used
    problem: str | None = None  # deemed basis needed but not computable

    def note(self, revenue: float) -> str | None:
        if not self.deemed:
            return None
        why = "; ".join(self.reasons)
        if self.npat is None:
            return f"NPAT targets need the Turnover basis (cl. 3.2.1: {why}). {self.problem}"
        src = (
            "a quarter of the industry norm (INTERPRETATION: no qualifying year given)"
            if self.interpretation
            else "the most recent year with a margin of at least a quarter of the industry norm"
        )
        return (
            f"Turnover basis (cl. 3.2.1: {why}): NPAT targets use deemed NPAT = "
            f"{self.margin_pct:g}% x {_rand(revenue)} = {_rand(self.npat)}, with the margin "
            f"from {src}."
        )


def _rand(x: float) -> str:
    return f"R{x:,.0f}".replace(",", " ")


def _finite(x: float | None) -> bool:
    return x is not None and math.isfinite(x)


def resolve(
    revenue: float,
    npat: float | None,
    npat_avg_5y: float | None = None,
    industry_norm_pct: float | None = None,
    qualifying_margin_pct: float | None = None,
) -> NpatBasis:
    """Decide which NPAT the NPAT-linked targets use.

    ``npat`` is last year's NPAT (may be negative). ``npat_avg_5y`` is the five-year average,
    ``industry_norm_pct`` the industry net profit margin norm (%), and
    ``qualifying_margin_pct`` the margin (%) of the most recent year in which it was at least
    a quarter of the norm. Raises ValueError for impossible inputs.
    """
    for name, v in (
        ("Industry norm", industry_norm_pct),
        ("Qualifying margin", qualifying_margin_pct),
    ):
        if v is not None and (not _finite(v) or v <= 0 or v > 100):
            raise ValueError(f"{name} must be a percentage above 0 and at most 100.")
    if npat_avg_5y is not None and not _finite(npat_avg_5y):
        raise ValueError("Five-year average NPAT must be a finite number.")
    if npat is not None and not _finite(npat):
        raise ValueError("NPAT must be a finite number.")

    reasons = []
    if npat is not None and npat <= 0:
        reasons.append("no profit last year")
    if npat_avg_5y is not None and npat_avg_5y <= 0:
        reasons.append("no profit on average over five years")
    quarter = industry_norm_pct / 4 if industry_norm_pct else None
    if (
        quarter is not None
        and npat is not None
        and npat > 0
        and revenue > 0
        and npat / revenue * 100 < quarter - 1e-12
    ):
        reasons.append(
            f"margin {npat / revenue * 100:.2f}% is below a quarter of the {industry_norm_pct:g}% "
            "industry norm"
        )
    if not reasons:
        return NpatBasis(npat if npat is not None and npat > 0 else None)

    if qualifying_margin_pct is not None:
        if quarter is not None and qualifying_margin_pct < quarter - 1e-12:
            raise ValueError(
                f"The qualifying year's margin ({qualifying_margin_pct:g}%) must be at least a "
                f"quarter of the industry norm ({quarter:g}%)."
            )
        margin, interp = qualifying_margin_pct, False
    elif quarter is not None:
        margin, interp = quarter, True
    else:
        return NpatBasis(
            None,
            deemed=True,
            reasons=tuple(reasons),
            problem="Enter the industry norm margin, or the margin of the most recent year in "
            "which it was at least a quarter of the norm.",
        )
    if revenue <= 0:
        return NpatBasis(
            None,
            deemed=True,
            reasons=tuple(reasons),
            margin_pct=margin,
            problem="Turnover must be above zero for the Turnover basis.",
        )
    return NpatBasis(
        margin / 100 * revenue,
        deemed=True,
        reasons=tuple(reasons),
        margin_pct=margin,
        interpretation=interp,
    )
