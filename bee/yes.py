"""YES Initiative (GG 41866, Notice 502). Preconditions cl. 2.1-2.4; recognition cl. 5.1.

Averages for the precondition use each priority element's achievement ratio: Ownership =
Net Value points / 8 (the sub-minimum measure), Skills = core points / max, ESD = core
points (PP + SD + ED, or PP + TF) / max. This interpretation is not specified in the
gazette and is flagged in results.
"""

from __future__ import annotations

from bee.models import EnterpriseSize, SubMinimumCheck, YesTier
from bee.submin import element_passed

LEVEL_STEPS = {YesTier.NONE: 0, YesTier.TARGET: 1, YesTier.TARGET_1_5X: 1, YesTier.TARGET_2X: 2}
BONUS_POINTS = {YesTier.TARGET_1_5X: 3.0}


def precondition(
    size: EnterpriseSize,
    checks: list[SubMinimumCheck],
    ratios: dict[str, float],
) -> tuple[bool, str | None]:
    if size == EnterpriseSize.EME:
        return True, None
    if size == EnterpriseSize.GENERIC:
        if all(c.passed for c in checks):
            return True, None
        avg = sum(ratios.values()) / max(len(ratios), 1)
        if avg >= 0.5 - 1e-9:
            return True, None
        return False, f"S6 cl. 2.1: sub-minimums not met and priority average {avg:.0%} < 50%"
    # QSE (cl. 2.2): 40% on Ownership + one other, or 40% average over Ownership + one other.
    own = element_passed(checks, "ownership")
    if own and (element_passed(checks, "skills") or element_passed(checks, "esd")):
        return True, None
    avg = (ratios.get("ownership", 0) + max(ratios.get("skills", 0), ratios.get("esd", 0))) / 2
    if avg >= 0.4 - 1e-9:
        return True, None
    return False, f"S6 cl. 2.2: QSE precondition not met (best average {avg:.0%} < 40%)"
