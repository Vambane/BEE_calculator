"""Scoring engine entry point. Order of steps (D3): total points (incl. YES +3) -> level
-> sub-minimum discount -> YES level uplift -> cap at Level 1."""

from __future__ import annotations

from bee import levels, submin, yes
from bee.indicators import element_group_points
from bee.models import EnterpriseSize, ScoreInput, ScoreResult, YesTier
from bee.registry import get_sector
from bee.rules import Scorecard
from bee.sectors.base import SectorConfig, SectorExcludedError


def calculate(inp: ScoreInput) -> ScoreResult:
    p = inp.profile
    cfg = get_sector(p.sector)
    if cfg.status == "excluded":
        raise SectorExcludedError(" ".join(cfg.warnings))
    variant = cfg.resolve_variant(p.variant)
    size = cfg.threshold(variant).classify(p.total_revenue)
    warnings = list(cfg.warnings)
    notes: list[str] = []

    deemed = None
    if size == EnterpriseSize.EME and not p.opt_scored:
        deemed = cfg.deemed_eme_level(p.black_ownership_pct)
    elif (
        size == EnterpriseSize.QSE
        and cfg.qse_deemed
        and p.black_ownership_pct >= 51
        and not p.opt_scored
    ):
        deemed = 1 if p.black_ownership_pct >= 100 else 2  # S5 cl. 5.3.1-5.3.2
    if deemed is not None:
        res = _deemed(cfg, size, deemed, inp, notes)
    else:
        res = _scored(size, cfg.card(size, variant), inp, notes)
    res.sector, res.variant, res.warnings = cfg.key, variant, warnings
    return res


def _deemed(cfg: SectorConfig, size, level, inp: ScoreInput, notes) -> ScoreResult:
    clause = "S5 cl. 4.3-4.4" if size == EnterpriseSize.EME else "S5 cl. 5.3"
    if cfg.key != "generic":
        clause = f"{cfg.name} sector code"
    notes.append(f"Deemed level ({clause}); evidence: sworn affidavit or CIPC certificate.")
    res = ScoreResult(size, level, 0, deemed=True, level_before_discount=level, notes=notes)
    if size == EnterpriseSize.EME and cfg.construction_eme_rules:
        level = _construction_eme(inp, level, res)
    res.level = level
    steps = yes.LEVEL_STEPS[inp.yes.tier]
    if steps:
        if size == EnterpriseSize.EME:
            res.level = levels.uplift(res.level, steps)
            res.yes_applied = True
        else:
            res.yes_blocked_reason = (
                "YES uplift for a deemed QSE requires scorecard measurement (opt_scored)"
            )
    res.recognition_pct = levels.recognition(res.level)
    return res


def _construction_eme(inp: ScoreInput, level: int, res: ScoreResult) -> int:
    """Construction cl. 3.6.2.4 (EME Skills obligation) and cl. 4.3 (enhancement)."""
    o, p = inp.options, inp.profile
    variant = p.variant or "contractor"
    exempt_below = 1_800_000 if variant == "bep" else 3_000_000
    pct = o.get("eme_skills_pct_of_qse_target")
    if bool(o.get("start_up")) or p.total_revenue < exempt_below:
        res.notes.append("Construction EME Skills obligation exempt (cl. 3.6.2.4.1-2).")
    elif pct is None:
        res.notes.append("Construction EME Skills obligation (cl. 3.6.2.4) not assessed.")
    elif float(pct) < 40:
        res.discounted = True
        res.notes.append("Construction EME below 40% of QSE Skills target: -1 level.")
        level = levels.discount(level)
    up = int(bool(o.get("eme_full_skills_points"))) + int(bool(o.get("eme_full_sd_points")))
    if up:
        res.notes.append(f"Construction EME enhancement cl. 4.3: +{up} level(s).")
        level = levels.uplift(level, up)
    return level


def _groups(card: Scorecard, inp: ScoreInput):
    draft = inp.draft_rules
    bonus: dict[str, float] = {}
    groups: dict[str, dict[str, float]] = {}
    for el in card.elements:
        if el.total is None:
            raw = element_group_points(el, inp.indicators.get(el.key, {}), inp.financials,
                                       draft)
        else:
            if inp.indicators.get(el.key):
                raise ValueError(
                    f"{card.key}/{el.key}: indicator inputs not available for this sector "
                    "scorecard (indicator tables not extracted); give points instead"
                )
            raw = {}
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
        for k in list(g):
            g[k] = max(0.0, min(g[k], el.max_points(k, draft=True)))
        if el.total is not None and sum(g.values()) > el.total:
            raise ValueError(f"{el.key}: points exceed the element weighting {el.total}")
        groups[el.key] = g
        b = max(0.0, b)
        if el.bonus_max is not None:
            b = min(b, el.bonus_max)
        bonus[el.key] = b
    tf_route = draft and groups.get("esd", {}).get("tf", 0) > 0
    if tf_route:
        groups["esd"]["sd"] = 0.0
        groups["esd"]["ed"] = 0.0
    core = {k: sum(v.values()) for k, v in groups.items()}
    return core, bonus, groups, tf_route


def _ratios(card: Scorecard, core, groups, draft, tf_route) -> dict[str, float]:
    r = {}
    if card.has("ownership"):
        own = card.element("ownership")
        if "net_value" in dict(own.group_max) or own.total is None:
            r["ownership"] = groups["ownership"].get("net_value", 0) / own.max_points(
                "net_value")
        else:
            r["ownership"] = core["ownership"] / own.max_points()
    if card.has("skills"):
        r["skills"] = core["skills"] / card.element("skills").max_points()
    if card.has("esd"):
        r["esd"] = core["esd"] / _esd_max(card, draft, tf_route)
    return r


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
    total = sum(element_points.values())
    checks = submin.evaluate(card, core, groups, draft, tf_route, inp.options)
    ratios = _ratios(card, core, groups, draft, tf_route)
    yes_ok, reason = (True, None)
    if tier != YesTier.NONE:
        yes_ok, reason = yes.precondition(size, checks, ratios)
    if yes_ok:
        total += yes.BONUS_POINTS.get(tier, 0.0)
    # 1) points -> 2) level (rescaled where the sector code requires it)
    level_points = total
    if card.level_base and inp.options.get(card.level_base_option or "", True) is not False:
        level_points = total * card.level_base / card.max_total()
        notes.append(
            f"Level from points normalised to {card.level_base:g}: {total:.2f} x "
            f"{card.level_base:g} / {card.max_total():g} = {level_points:.2f}."
        )
    lvl = levels.level_from_points(round(level_points, 6))
    before = lvl
    # 3) discount (one level for any or a combination of failures)
    discounted = not submin.compliant(card, checks)
    if discounted:
        lvl = levels.discount(lvl)
    # 4) YES uplift 5) cap at L1
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
    for c in checks:
        if c.option_used:
            notes.append(c.option_used)
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
        scorecard=card.key,
        level_points=round(level_points, 4),
    )


def _esd_max(card: Scorecard, draft: bool, tf_route: bool) -> float:
    esd = card.element("esd")
    if esd.total is not None:
        return esd.max_points()
    if tf_route:
        return esd.max_points("pp") + esd.max_points("tf", draft=True)
    return esd.max_points("pp") + esd.max_points("sd") + esd.max_points("ed")


def max_points(card: Scorecard) -> float:
    """Core maximum (bonuses and draft-only indicators excluded)."""
    return card.max_total()
