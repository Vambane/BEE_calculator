"""Indicator tables for the sector scorecards, loaded from Compliance's
``data/sector-element-targets.csv`` (23 Oct 2026; GG 41287 N931/N1325, GG 41306, GG 39430).

Each sector element keeps its gazetted weighting (``Element.total``/``group_max``) and gains
``indicators`` so it can take raw indicator values as well as pre-computed points.

Parsing rules (documented in ``CSV_NOTES``):
- target ``Yes`` -> yes/no indicator; ``% of NPAT`` -> NPAT base; ``% LA`` / ``leviable`` ->
  leviable amount; ``% employees`` -> headcount; procurement rows -> TMPS.
- Phase-in targets ("32.5% (35% yr4)", "75% (yr1-3) / 80% (yr3+)") use the first figure.
- Targets that are not a plain percentage (Annexe formulas, EAP shares, rand-billion
  targets, "% of value in 2.3.1"...) take "% of target achieved" (target 100).
"""

from __future__ import annotations

import csv
import re
from dataclasses import replace
from functools import cache
from pathlib import Path

from bee.rules import Indicator, Scorecard

CSV_PATH = Path(__file__).parent / "data" / "sector-element-targets.csv"
CSV_NOTES = (
    "Sector indicator targets from Compliance's sector-element-targets table: phase-in "
    "targets use the first (year-1) figure; non-percentage targets (Annexe formulas, EAP, "
    "rand amounts) are entered as % of target achieved."
)

_NUM = re.compile(r"(\d+(?:\.\d+)?)\s*%")


@cache
def rows() -> tuple[dict[str, str], ...]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return tuple(csv.DictReader(f))


def _element_key(el: str) -> str:
    e = el.lower()
    if e.startswith("ownership"):
        return "ownership"
    if e.startswith("management"):
        return "management"
    if e.startswith("skills"):
        return "skills"
    if e.startswith("sed"):
        return "sed"
    if e.startswith("access to financial"):
        return "afs"
    if e.startswith("empowerment financing"):
        return "ef"
    return "esd"


def _group(row: dict[str, str], key: str) -> str:
    el, clause, name = row["element"].lower(), row["clause"], row["indicator"]
    if key == "ownership":
        return "net_value" if "net value" in name.lower() else "main"
    if key == "ef":
        if clause.startswith("FS600 2.3"):
            return "sd"
        if clause.startswith("FS600 2.4"):
            return "ed"
        return "ef"
    if key != "esd":
        return "main"
    sub = el.split(":", 1)[-1].strip()
    if "programmes" in sub:
        return "sd_programmes"
    if "contributions" in sub:
        return "sd_contributions"
    if sub in ("sd", "supplier development"):
        return "sd"
    if sub in ("ed", "enterprise development"):
        return "ed"
    return "pp"  # PP / Procurement / Preferential Procurement / Bonus


def _target_base(row: dict[str, str], group: str) -> tuple[float, str, str]:
    """Return (target, base, display-name suffix)."""
    t, name = row["target"].strip(), row["indicator"]
    if t.lower() == "yes":
        return 0.0, "bool", ""
    m = _NUM.search(t)
    if "npat" in t.lower() and m and " of value" not in t:
        return float(m.group(1)), "npat", ""
    relative = (
        not m
        or t.lower().startswith(("annexe", "formula", "see", "eap"))
        or " of " in t.replace("% of NPAT", "")
        or "@" in t
        or "TBD" in t
    )
    if relative:
        return 100.0, "pct", " (% of target achieved)"
    target = float(m.group(1))
    low = name.lower()
    if (
        ("% la" in low or "leviable" in low)
        and "at level" not in low
        and not name.startswith("...")
    ):
        return target, "leviable", ""
    if "% employees" in low or "% of employees" in low:
        return target, "employees", ""
    if group == "pp" and ("pp" in low or "spend" in low):
        return target, "tmps", ""
    return target, "pct", ""


def indicators(sector: str, scorecards: dict[str, tuple[str, ...]]) -> dict[str, tuple]:
    """{element key: tuple[Indicator]} for one card. ``scorecards`` maps an element key
    (or "*") to the CSV scorecard labels to take rows from."""
    out: dict[str, list[Indicator]] = {}
    for r in rows():
        if r["sector"] != sector:
            continue
        key = _element_key(r["element"])
        labels = scorecards.get(key, scorecards.get("*", ()))
        if r["scorecard"] not in labels:
            continue
        pts = float(r["points"])
        if pts == 0:
            continue
        group = _group(r, key)
        target, base, suffix = _target_base(r, group)
        out.setdefault(key, []).append(
            Indicator(
                r["clause"],
                r["indicator"] + suffix,
                pts,
                target,
                base,
                group,
                bonus=r["bonus"].upper() == "Y",
            )
        )
    return {k: tuple(v) for k, v in out.items()}


def attach(
    card: Scorecard,
    sector: str,
    scorecards: dict[str, tuple[str, ...]],
    overrides: dict[str, float] | None = None,
) -> Scorecard:
    """Return ``card`` with CSV indicators attached to its element-level elements.
    ``overrides`` replaces targets by clause (variant-specific targets)."""
    table = indicators(sector, scorecards)
    els = []
    for e in card.elements:
        inds = table.get(e.key)
        if inds and overrides:
            inds = tuple(replace(i, target=overrides.get(i.clause, i.target)) for i in inds)
        if inds:
            bonus = sum(i.points for i in inds if i.bonus)
            e = replace(e, indicators=inds, bonus_max=max(e.bonus_max or 0.0, bonus))
        els.append(e)
    return replace(card, elements=tuple(els))


def check_reconciles(card: Scorecard) -> list[str]:
    """Element weightings vs. the sum of non-bonus indicator points (for tests)."""
    bad = []
    for e in card.elements:
        if e.total is None or not e.indicators:
            continue
        core = sum(i.points for i in e.indicators if not i.bonus)
        if abs(core - e.total) > 1e-9:
            bad.append(f"{card.key}/{e.key}: indicators {core:g} vs weighting {e.total:g}")
        for g, cap in e.group_max:
            gs = sum(i.points for i in e.indicators if not i.bonus and i.group == g)
            if abs(gs - cap) > 1e-9:
                bad.append(f"{card.key}/{e.key}.{g}: indicators {gs:g} vs {cap:g}")
    return bad
