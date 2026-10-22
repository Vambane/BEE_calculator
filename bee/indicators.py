"""Score indicators from raw values: percentages, rand amounts or yes/no flags."""

from __future__ import annotations

from bee.models import Financials, IndicatorValue, Rand
from bee.rules import Element, Indicator

_BASE_ATTR = {
    "npat": "npat",
    "leviable": "leviable_amount",
    "tmps": "tmps",
    "employees": "employees",
}


def _finite_nonneg(clause: str, amount: float, what: str = "value") -> float:
    if amount != amount or amount in (float("inf"), float("-inf")):  # NaN / inf
        raise ValueError(f"{clause}: {what} must be a finite number")
    if amount < 0:
        raise ValueError(f"{clause}: {what} cannot be negative")
    return amount


def to_percent(ind: Indicator, value: IndicatorValue, fin: Financials) -> float:
    """Return the achieved percentage. Rand amounts are divided by the indicator's base."""
    if isinstance(value, Rand):
        attr = _BASE_ATTR.get(ind.base)
        if attr is None:
            raise ValueError(f"{ind.clause}: rand amount given but indicator base is {ind.base}")
        base = getattr(fin, attr)
        if not base or base <= 0:
            # Negative or zero NPAT etc.: no meaningful %; caller should pass a percentage.
            raise ValueError(f"{ind.clause}: Financials.{attr} must be > 0 to use a rand amount")
        return _finite_nonneg(ind.clause, value.amount, "rand amount") / base * 100
    if isinstance(value, bool):
        raise ValueError(f"{ind.clause}: boolean given for a non-boolean indicator")
    return _finite_nonneg(ind.clause, float(value))


def indicator_points(
    ind: Indicator, value: IndicatorValue, fin: Financials, draft: bool = False
) -> float:
    points = ind.draft_points if draft and ind.draft_points is not None else ind.points
    if ind.base == "bool":
        return points if bool(value) else 0.0
    pct = to_percent(ind, value, fin)
    if pct <= 0 or ind.target <= 0:
        return 0.0
    return min(pct / ind.target, 1.0) * points


def element_group_points(
    element: Element,
    values: dict[str, IndicatorValue],
    fin: Financials,
    draft: bool = False,
) -> dict[str, dict[str, float]]:
    """Return {group: {"points": core, "bonus": bonus}} for one element."""
    known = {i.clause for i in element.indicators}
    unknown = set(values) - known
    if unknown:
        raise KeyError(f"{element.key}: unknown indicator clause(s) {sorted(unknown)}")
    out: dict[str, dict[str, float]] = {}
    for ind in element.indicators:
        if ind.draft_only and not draft:
            continue
        g = out.setdefault(ind.group, {"points": 0.0, "bonus": 0.0})
        if ind.clause not in values:
            continue
        pts = indicator_points(ind, values[ind.clause], fin, draft)
        g["bonus" if ind.bonus else "points"] += pts
    return out
