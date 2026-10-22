"""Priority-element sub-minimums and discounting (S5 cl. 3.3)."""

from __future__ import annotations

from bee.models import SubMinimumCheck
from bee.rules import Scorecard


def evaluate(
    card: Scorecard,
    element_points: dict[str, float],
    group_points: dict[str, dict[str, float]],
    draft: bool = False,
    tf_route: bool = False,
    options: dict | None = None,
) -> list[SubMinimumCheck]:
    options = options or {}
    checks = []
    for sm in card.submins:
        if sm.draft_only and not (draft and tf_route):
            continue
        if sm.replaced_by_draft and draft and tf_route:
            continue
        if sm.group is None:
            achieved = element_points.get(sm.element, 0.0)
        else:
            achieved = group_points.get(sm.element, {}).get(sm.group, 0.0)
        required, used = sm.required, None
        if sm.option_key and sm.option_key in options:
            required = float(options[sm.option_key])
            used = f"Sub-minimum {sm.element} overridden by option {sm.option_key}={required:g}."
        elif sm.option_key:
            used = (f"Interpretation: {sm.element} sub-minimum {required:g} ({sm.clause}); "
                    f"configurable via options['{sm.option_key}'].")
        checks.append(
            SubMinimumCheck(sm.element, sm.group, achieved, required, sm.clause, used)
        )
    return checks


def element_passed(checks: list[SubMinimumCheck], element: str) -> bool:
    return all(c.passed for c in checks if c.element == element)


def compliant(card: Scorecard, checks: list[SubMinimumCheck]) -> bool:
    """True when the priority-element rule is satisfied (no discount)."""
    if card.priority_rule == "all":
        return all(c.passed for c in checks)
    if card.priority_rule == "ownership_plus_one":
        return element_passed(checks, "ownership") and (
            element_passed(checks, "skills") or element_passed(checks, "esd")
        )
    raise ValueError(card.priority_rule)
