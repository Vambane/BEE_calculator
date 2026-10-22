"""Scoring engine entry point. Order of steps (D3): total points (incl. YES +3) -> level
-> sub-minimum discount -> YES level uplift -> cap at Level 1."""

from __future__ import annotations

from bee import levels, submin, yes
from bee.indicators import element_group_points
from bee.models import EnterpriseSize, ScoreInput, ScoreResult, YesTier
from bee.registry import DEFAULT_SECTOR, get_scorecard
from bee.rules import Scorecard
from bee.scorecards.eme import deemed_level
from bee.sizing import classify


def calculate(inp: ScoreInput) -> ScoreResult:
    p = inp.profile
    size = classify(p.total_revenue)
    notes: list[str] = []
    if p.sector.lower() != DEFAULT_SECTOR:
        notes.append(f"Sector {p.sector!r}: using the registered sector scorecard.")

    deemed = None
    if size == EnterpriseSize.EME and not p.opt_scored:
        deemed = deemed_level(p.black_ownership_pct)
    elif size == EnterpriseSize.QSE and p.black_ownership_pct >= 51 and not p.opt_scored:
        deemed = 1 if p.black_ownership_pct >= 100 else 2  # S5 cl. 5.3.1-5.3.2
    if deemed is not None:
        return _deemed(size, deemed, inp, notes)

    card = get_scorecard(size, p.sector)
    return _scored(size, card, inp, notes)


def _deemed(size, level, inp: ScoreInput, notes) -> ScoreResult:
    clause = "S5 cl. 4.3-4.4" if size == EnterpriseSize.EME else "S5 cl. 5.3"
    notes.append(f"Deemed level ({clause}); evidence: sworn affidavit or CIPC certificate.")
    res = ScoreResult(size, level, 0, deemed=True, level_before_discount=level, notes=notes)
    steps = yes.LEVEL_STEPS[inp.yes.tier]
    if steps:
        ok, reason = (True, None) if size == EnterpriseSize.EME else (
            False, "YES uplift for a deemed QSE requires scorecard measurement (opt_scored)")
        if ok:
            res.level = levels.uplift(level, steps)
            res.yes_applied = True
        res.yes_blocked_reason = reason
    res.recognition_pct = levels.recognition(res.level)
    return res


def _groups(card: Scorecard, inp: ScoreInput):
    """Return (element core points, element bonus points, group core points)."""
    draft = inp.draft_rules
    core: dict[str, float] = {}
    bonus: dict[str, float] = {}
    groups: dict[str, dict[str, float]] = {}
    for el in card.elements:
        raw = element_group_points(el, inp.indicators.get(el.key, {}), inp.financials, draft)
        g = {k: v["points"] for k, v in raw.items()}
        b = sum(v["bonus"] for v in raw.values())
        given = dict(inp.points.get(el.key, {}))
        if given:
            b = given.pop("bonus", b)
            total = given.pop("total", None)
            for k, v in given.items():
                if k not in el.groups():
                    raise KeyError(f"{el.key}: unknown group {k!r}; groups are {el.groups()}")
                g[k] = float(v)
            if total is not None:
                other = sum(v for k, v in given.items() if k != "main")
                g["main"] = float(total) - other
        if not draft:
            g.pop("tf", None)
        # cap each group at its maximum
        for k in list(g):
            g[k] = max(0.0, min(g[k], el.max_points(k, draft=True)))
        groups[el.key] = g
        bonus[el.key] = max(0.0, b)
    tf_route = draft and groups.get("esd", {}).get("tf", 0) > 0
    if tf_route:
        # Draft S400 cl. 3.2.3: TF is an alternative to SD + ED (read as mutually exclusive).
        groups["esd"]["sd"] = 0.0
        groups["esd"]["ed"] = 0.0
    for el in card.elements:
        core[el.key] = sum(groups[el.key].values())
    return core, bonus, groups, tf_route


def _scored(size, card: Scorecard, inp: ScoreInput, notes) -> ScoreResult:
    draft = inp.draft_rules
    if draft:
        notes.append("DRAFT rules on: Transformation Fund per Draft S400 2026 (not law).")
    elif inp.indicators.get("esd", {}).get("draft400 2.4.1") or inp.points.get("esd", {}).get(
        "tf"
    ):
        notes.append("Transformation Fund input ignored: draft rules flag is off (D4).")
    core, bonus, groups, tf_route = _groups(card, inp)
    element_points = {k: core[k] + bonus[k] for k in core}

    tier = inp.yes.tier
    yes_points = yes.BONUS_POINTS.get(tier, 0.0)
    total = sum(element_points.values())
    # 1) points (YES +3 counted only when the precondition holds; checked below)
    checks = submin.evaluate(card, core, groups, draft, tf_route)
    ratios = {
        "ownership": groups["ownership"].get("net_value", 0) / 8,
        "skills": core["skills"] / card.element("skills").max_points(),
        "esd": core["esd"] / _esd_max(card, draft, tf_route),
    }
    yes_ok, reason = (True, None)
    if tier != YesTier.NONE:
        yes_ok, reason = yes.precondition(size, checks, ratios)
    if yes_ok and yes_points:
        total += yes_points
    # 2) level
    lvl = levels.level_from_points(total)
    before = lvl
    # 3) discount: one level for any or a combination of failures (S5 cl. 3.3.3.1)
    discounted = not submin.compliant(card, checks)
    if discounted:
        lvl = levels.discount(lvl)
    # 4) YES uplift  5) cap at L1
    applied = False
    if tier != YesTier.NONE and yes_ok:
        prev = inp.yes.previous_level
        if prev is not None and lvl > prev:
            yes_ok, reason = False, "S6 cl. 2.4: entity did not maintain its previous level"
        else:
            lvl = levels.uplift(lvl, yes.LEVEL_STEPS[tier])
            applied = True
    if tier != YesTier.NONE:
        notes.append("YES precondition averages use the engine's ratio interpretation.")
    return ScoreResult(
        size=size,
        level=lvl,
        recognition_pct=levels.recognition(lvl),
        total_points=round(total, 4),
        element_points=element_points,
        group_points=groups,
        level_before_discount=before,
        discounted=discounted,
        submin_checks=checks,
        yes_applied=applied,
        yes_blocked_reason=reason,
        notes=notes,
    )


def _esd_max(card: Scorecard, draft: bool, tf_route: bool) -> float:
    esd = card.element("esd")
    if tf_route:
        return esd.max_points("pp") + esd.max_points("tf", draft=True)
    return esd.max_points("pp") + esd.max_points("sd") + esd.max_points("ed")


def max_points(card: Scorecard) -> float:
    """Core maximum (bonuses and draft-only indicators excluded)."""
    return sum(e.max_points() for e in card.elements)
