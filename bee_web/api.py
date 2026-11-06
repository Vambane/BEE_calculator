"""JSON API over the scoring engine for the browser build (runs in Pyodide).

The web front end owns one *session* object and sends it with every call::

    {"store": <canonical store, see bee_ui.core.fresh_store>,
     "sector": "generic", "draft": false, "default_mode": "rand"}

``store`` is exactly what a client file holds, so saving and opening files needs no mapping.
Every function here is pure: it reads the session, calls the engine (``bee`` and
``bee_ui``) and returns plain JSON-safe data. No scoring rule lives in this module or in the
front end; this file only reshapes what the engine already computes, mirroring ``app.py``.

Entry point for the worker: ``call(name, args_json) -> result_json``.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace as dc_replace
from datetime import date
from typing import Any

from bee import EnterpriseSize, Financials, Rand, calculate
from bee.contributions import COLUMNS as CONTRIB_COLUMNS
from bee.contributions import TYPES as CONTRIB_TYPES
from bee.contributions import parse_rows as parse_contributions
from bee.contributions import summarise as summarise_contributions
from bee.contributions import targets as contrib_targets
from bee.indicators import indicator_points
from bee.levels import LEVELS
from bee.net_value import DEFAULT_TARGET as NV_TARGET
from bee.net_value import NetValueInput, graduation_factor, measurement_year
from bee.net_value import calculate as calculate_net_value
from bee.npat import resolve as resolve_npat
from bee.procurement import COLUMNS as PROC_COLUMNS
from bee.procurement import EXCLUSIONS as PROC_EXCLUSIONS
from bee.procurement import (
    LEVEL_OPTIONS,
    procurement_indicators,
    summarise,
    template_csv,
    to_record,
)
from bee.procurement import SIZES as PROC_SIZES
from bee.procurement import parse_csv as proc_parse_csv
from bee.procurement import parse_rows as proc_parse_rows
from bee.procurement import to_csv as proc_to_csv
from bee.registry import get_sector
from bee.report import SUBMIN_GROUP_LABELS, _report_context, num
from bee_ui import client_file
from bee_ui.core import (
    BASE_FIN,
    BASE_LABEL,
    PCT_ONLY_ELEMENTS,
    build_input,
    card_for,
    default_entry_mode,
    entry_options,
    fresh_store,
    gender_contribution,
    gender_open_gaps,
    indicator_render_units,
    next_level_gap,
    rand_capable,
    scorecard_label,
    scorecard_max,
    sector_choices,
    size_for,
    to_pct,
    to_rand,
    validate,
    visible_indicators,
)

DRAFT_LABEL = "Draft 2026 rules (Transformation Fund)"
MAX_SUPPLIER_CSV_BYTES = 2_000_000


# ------------------------------------------------------------------ helpers
def _num(v: Any) -> float | None:
    if isinstance(v, bool) or v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _clean(obj: Any) -> Any:
    """JSON-safe copy: non-finite floats become None, dates become ISO strings."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple | set):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, date):
        return obj.isoformat()
    if hasattr(obj, "value") and not isinstance(obj, bool | int | float | str):
        return obj.value  # enums
    return obj


def _display(obj: Any) -> Any:
    """Display copy of an already-clean result: '>=' in rule names reads as '≥'."""
    if isinstance(obj, dict):
        return {k: _display(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_display(v) for v in obj]
    if isinstance(obj, str):
        return obj.replace(">=", "≥")
    return obj


def _rand_text(x: float) -> str:
    return f"R{x:,.0f}".replace(",", " ")


def _date(v: Any) -> date | None:
    if isinstance(v, date):
        return v
    if isinstance(v, str) and v:
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


class _Session:
    """Read-side view of the session the browser sends (mirrors app.py's module state)."""

    def __init__(self, sess: dict):
        self.store: dict = sess.get("store") or fresh_store()
        valid = dict(sector_choices())
        sector = sess.get("sector") or "generic"
        self.sector: str = sector if sector in valid else "generic"
        self.draft: bool = bool(sess.get("draft"))
        self.default_mode: str = "pct" if sess.get("default_mode") == "pct" else "rand"
        self.cfg = get_sector(self.sector)
        p = self.store["profile"]
        variant = p.get("variant") if self.cfg.variants else None
        if variant not in (self.cfg.variants or (None,)):
            variant = self.cfg.default_variant
        self.variant = variant
        try:
            self.size = size_for(self.cfg, p.get("revenue") or 0.0, variant)
        except ValueError:
            self.size = EnterpriseSize.EME
        opt_scored = bool(p.get("opt_scored"))
        self.card = (
            card_for(self.cfg, self.size, variant)
            if (self.size.value != "EME" or opt_scored)
            else None
        )
        self.elements = [e for e in self.card.elements if e.max_points() > 0] if self.card else []
        self.label = scorecard_label(self.cfg, self.size, variant)

    # app.py fin_obj()
    def fin(self, effective: bool = True) -> Financials:
        f = self.store["fin"]
        fin = Financials(
            npat=f.get("npat") or None,
            leviable_amount=f.get("leviable_amount") or None,
            tmps=f.get("tmps") or None,
            employees=f.get("employees") or None,
            npat_avg_5y=f.get("npat_avg_5y"),
            industry_norm_margin_pct=f.get("industry_norm_margin_pct") or None,
            qualifying_margin_pct=f.get("qualifying_margin_pct") or None,
        )
        if not effective:
            return fin
        basis = self.npat_basis(fin)
        if basis is None or not basis.deemed:
            return fin
        return dc_replace(fin, npat=basis.npat)

    def npat_basis(self, fin: Financials):
        try:
            return resolve_npat(
                float(self.store["profile"].get("revenue") or 0.0),
                fin.npat,
                fin.npat_avg_5y,
                fin.industry_norm_margin_pct,
                fin.qualifying_margin_pct,
            )
        except ValueError:
            return None

    def element(self, key: str):
        return next((e for e in self.elements if e.key == key), None)

    def mode(self, el) -> str:
        return self.store["modes"].get(el.key, "pct")

    def values(self) -> dict:
        return {
            e.key: self.store["values"][self.store["modes"].get(e.key, "pct")].get(e.key, {})
            for e in self.elements
        }

    def current_input(self, esd_override: dict | None = None):
        inp = build_input(
            self.sector,
            self.variant,
            self.store["profile"],
            self.fin(effective=False),
            self.values(),
            self.store["modes"],
            self.store["points"],
            self.draft,
            self.store["options"],
            self.store["entry"],
        )
        if esd_override is not None:
            row = {
                k: v
                for k, v in inp.indicators.get("esd", {}).items()
                if k not in esd_override["drop"]
            }
            row.update(esd_override["add"])
            inp.indicators["esd"] = row
        return inp

    def validation_card(self):
        card = self.card
        if card is None and self.cfg.cards:
            card = card_for(self.cfg, self.size, self.store["profile"].get("variant"))
        return card


# ------------------------------------------------------------------ static metadata
def meta() -> dict:
    """Everything the UI needs once at start-up."""
    return {
        "sectors": [{"key": k, "name": n} for k, n in sector_choices()],
        "fresh_store": _clean(fresh_store()),
        "draft_label": DRAFT_LABEL,
        "level_options": list(LEVEL_OPTIONS),
        "proc": {
            "columns": [label for _, label in PROC_COLUMNS],
            "sizes": list(PROC_SIZES),
            "exclusions": list(PROC_EXCLUSIONS.values()),
            "max_csv_bytes": MAX_SUPPLIER_CSV_BYTES,
        },
        "contrib": {"columns": [label for _, label in CONTRIB_COLUMNS]},
        "net_value_target": NV_TARGET,
        "client_file": {
            "format": client_file.FORMAT,
            "version": client_file.VERSION,
            "max_bytes": client_file.MAX_BYTES,
        },
        "yes_tiers": ["none", "target", "1.5x", "2x"],
        "levels": [{"min": m, "level": lv, "recognition": rec} for m, lv, rec in LEVELS],
    }


def fresh() -> dict:
    return _clean(fresh_store())


# ------------------------------------------------------------------ context (steps, forms)
def _indicator(el, i, mode: str) -> dict:
    rand = mode == "rand" and rand_capable(el, i)
    tag = " (DRAFT)" if i.draft_only else (" (bonus)" if i.bonus else "")
    if i.base == "bool":
        unit = None
    elif rand:
        unit = "count" if i.base == "employees" else "R"
    elif i.base in BASE_LABEL:
        unit = f"% of {BASE_LABEL[i.base]}"
    else:
        unit = "%"
    women = "women" in i.name.lower() or "female" in i.name.lower()
    target_text = "Yes" if i.base == "bool" else f"{num(i.target)}%"
    pts = f"{num(i.points)} {'pt' if i.points == 1 else 'pts'}"
    help_text = (
        f"{pts} if met · cl. {i.clause}"
        if i.base == "bool"
        else f"Target {target_text} · {pts} · cl. {i.clause}"
    )
    if women:
        help_text += (
            " · scored on its own line (also counted inside Black people for ownership rules)"
        )
    return {
        "clause": i.clause,
        "name": i.name.replace(">=", "≥"),
        "tag": tag.strip(" ()") or None,
        "kind": "bool" if i.base == "bool" else "number",
        "unit": unit,
        "rand": rand,
        "target": i.target,
        "target_text": target_text,
        "points": i.points,
        "points_text": pts,
        "bonus": i.bonus,
        "draft_only": i.draft_only,
        "group": i.group,
        "women_line": women,
        "help": help_text,
    }


def _element_spec(s: _Session, el) -> dict:
    draft = s.draft
    opts = entry_options(el)
    entry = s.store["entry"].get(el.key, default_entry_mode(el))
    can_rand = el.key not in PCT_ONLY_ELEMENTS and any(rand_capable(el, i) for i in el.indicators)
    mode = s.store["modes"].get(el.key, s.default_mode if can_rand else "pct")
    if not can_rand:
        mode = "pct"
    units = []
    for u in indicator_render_units(el, draft):
        if u["kind"] == "pair":
            units.append(
                {
                    "kind": "pair",
                    "heading": u["heading"],
                    "labels": list(u["labels"]),
                    "black": _indicator(el, u["black"], mode),
                    "women": _indicator(el, u["women"], mode),
                }
            )
        else:
            units.append(
                {
                    "kind": "single",
                    "women_owned": bool(u.get("women_owned")),
                    "ind": _indicator(el, u["ind"], mode),
                }
            )
    covered = el.total is not None and sum(dict(el.group_max).values()) >= el.total
    groups = [
        {
            "key": g,
            "label": "Points" if g == "main" else g.replace("_", " ").title() + " points",
            "max": el.max_points(g, draft),
        }
        for g in el.groups()
        if (draft or g != "tf") and not (g == "main" and covered) and el.max_points(g, draft) > 0
    ]
    bmax = (
        el.bonus_max
        if el.bonus_max is not None
        else sum(i.points for i in el.indicators if i.bonus)
    )
    nv = next((i for i in el.indicators if i.group == "net_value"), None)
    nvs = next((x for x in s.card.submins if x.group == "net_value"), None) if nv else None
    used = sorted({i.base for i in el.indicators if rand_capable(el, i)})
    fin = s.fin()
    return {
        "key": el.key,
        "name": el.name,
        "max": el.max_points(draft=draft),
        "entry_options": opts,
        "entry": entry,
        "can_rand": can_rand,
        "mode": mode,
        "units": units,
        "point_groups": groups,
        "bonus_max": bmax or 0,
        "net_value": None
        if nv is None
        else {
            "clause": nv.clause,
            "points": nv.points,
            "submin": nvs.required if nvs else None,
        },
        "procurement": bool(procurement_indicators(el)),
        "contributions": [t.label for t in (contrib_targets(s.card, el.key) or [])],
        "submins": [
            {
                "group": SUBMIN_GROUP_LABELS.get(x.group, x.group) if x.group else None,
                "required": x.required,
                "clause": x.clause,
            }
            for x in s.card.submins
            if x.element == el.key and (draft or not x.draft_only)
        ],
        "bases": [
            {"label": BASE_LABEL[b], "value": getattr(fin, BASE_FIN[b]) or 0.0} for b in used
        ],
        "eap_note": el.key == "management",
    }


def context(session: dict) -> dict:
    """Steps, scorecard label and per-element form specs (app.py context() + element_step)."""
    s = _Session(session)
    cfg = s.cfg
    fin_raw = s.fin(effective=False)
    basis = s.npat_basis(fin_raw)
    if basis is None:
        try:
            resolve_npat(
                float(s.store["profile"].get("revenue") or 0.0),
                fin_raw.npat,
                fin_raw.npat_avg_5y,
                fin_raw.industry_norm_margin_pct,
                fin_raw.qualifying_margin_pct,
            )
            low = None
        except ValueError as exc:
            low = {"state": "error", "text": str(exc)}
    elif not basis.deemed:
        low = {"state": "npat", "text": "NPAT basis applies: targets use last year's NPAT."}
    elif basis.npat is None:
        low = {
            "state": "warning",
            "text": f"Turnover basis applies ({'; '.join(basis.reasons)}). {basis.problem}",
        }
    else:
        low = {"state": "info", "text": basis.note(float(s.store["profile"].get("revenue") or 0.0))}
    status = cfg.status
    badge = None
    sector_warning = None
    if status == "verified" and cfg.key != "generic":
        badge = "Verified sector code"
    elif status == "unverified":
        badge = "Pending expert verification"
        sector_warning = "This sector scorecard is not yet verified; treat results as indicative."
    elif status in ("not_loaded", "legacy"):
        sector_warning = (
            f"No verified {cfg.name} scorecard in this version: Generic targets are applied "
            "(fallback)."
        )
    out_of = scorecard_max(s.card, s.draft) if s.card else None
    return _clean(
        {
            "sector": s.sector,
            "sector_name": cfg.name,
            "variants": list(cfg.variants or []),
            "variant": s.variant,
            "size": cfg.size_labels.get(s.size, s.size.value),
            "label": s.label,
            "badge": badge,
            "sector_warning": sector_warning,
            "out_of": out_of,
            "has_card": s.card is not None,
            "steps": [{"key": "profile", "name": "Profile"}]
            + [{"key": e.key, "name": e.name} for e in s.elements]
            + [{"key": "results", "name": "Results"}],
            "elements": {e.key: _element_spec(s, e) for e in s.elements},
            "low_profit": low,
            "financial_options": s.sector == "financial",
            "tf_card": any(i.group == "tf" for e in s.elements for i in e.indicators),
        }
    )


# ------------------------------------------------------------------ validation
def problems(session: dict, step: str) -> list[str]:
    """Messages that block Continue on a step ('profile' or an element key)."""
    s = _Session(session)
    store = s.store
    if step == "profile":
        out = [] if store.get("consent") else ["Tick the privacy consent box to continue."]
        out += [
            p.message for p in validate(s.validation_card(), store["profile"], s.fin(), {}, {}, {})
        ]
        return out
    el = s.element(step)
    if el is None:
        return []
    ent = store["entry"].get(el.key, default_entry_mode(el))
    return [
        p.message
        for p in validate(
            s.card,
            store["profile"],
            s.fin(),
            {el.key: store["values"][store["modes"].get(el.key, "pct")].get(el.key, {})}
            if ent == "ind"
            else {},
            store["modes"],
            {el.key: store["points"].get(el.key, {})} if ent == "pts" else {},
        )
    ]


# ------------------------------------------------------------------ rand <-> % conversion
def convert_mode(session: dict, element: str, new_mode: str) -> dict:
    """Switch an element between rand and % entry, converting entered values through the
    profile bases (app.py element_step). Returns the updated store."""
    s = _Session(session)
    el = s.element(element)
    store = s.store
    if el is None or new_mode not in ("rand", "pct"):
        return _clean(store)
    mode = store["modes"].get(el.key, s.default_mode)
    if mode != new_mode:
        fin = s.fin()
        src = store["values"][mode].get(el.key, {})
        dst = store["values"][new_mode].setdefault(el.key, {})
        for i in el.indicators:
            if i.clause in src and rand_capable(el, i) and not isinstance(src[i.clause], bool):
                base = getattr(fin, BASE_FIN[i.base])
                dst[i.clause] = (to_rand if new_mode == "rand" else to_pct)(
                    float(src[i.clause] or 0.0), base
                )
    store["modes"][el.key] = new_mode
    return _clean(store)


# ------------------------------------------------------------------ results
def _tips(el, draft: bool) -> list[dict]:
    return [
        {
            "name": t.name,
            "target": f"{num(t.target)}{'' if t.base == 'bool' else '%'}",
            "points": t.points,
            "clause": t.clause,
        }
        for t in sorted(
            (x for x in visible_indicators(el, draft) if not x.bonus), key=lambda x: -x.points
        )[:2]
    ]


def score(session: dict) -> dict:
    """Validate everything and score (app.py results_step)."""
    s = _Session(session)
    store = s.store
    if not store.get("consent"):
        return {"ok": False, "problems": ["Tick the privacy consent box to continue."]}
    values = s.values()
    ind_vals = {k: v for k, v in values.items() if store["entry"].get(k, "ind") == "ind"}
    pts_vals = {k: v for k, v in store["points"].items() if store["entry"].get(k) == "pts"}
    probs = validate(
        s.validation_card(), store["profile"], s.fin(), ind_vals, store["modes"], pts_vals
    )
    if probs:
        return {"ok": False, "problems": [p.message for p in probs]}
    inp = s.current_input()
    r = calculate(inp)
    card = s.card
    out_of = scorecard_max(card, s.draft) if card else None
    gap = None if r.deemed or r.level_points is None else next_level_gap(r.level_points)
    gender = None
    if not r.deemed and card:
        gx, gy = gender_contribution(card, inp.indicators, inp.financials, s.draft)
        if gy > 0:
            gender = {"achieved": gx, "max": gy}
    rows = []
    for e in s.elements:
        mx = e.max_points(draft=s.draft)
        pts = r.element_points.get(e.key, 0.0)
        rows.append(
            {
                "key": e.key,
                "name": e.name,
                "points": pts,
                "max": mx,
                "gap": max(mx - pts, 0.0),
                "tips": _tips(e, s.draft),
                "submin_failed": any(c.element == e.key and not c.passed for c in r.submin_checks),
            }
        )
    names = {e.key: e.name for e in s.elements}
    return _display(
        _clean(
            {
                "ok": True,
                "level": r.level,
                "level_label": r.level_label,
                "recognition_pct": r.recognition_pct,
                "deemed": r.deemed,
                "total": r.total_points,
                "out_of": out_of,
                "level_points": r.level_points,
                "next_gap": {"points": gap[0], "level": gap[1]} if gap else None,
                "gender": gender,
                "discounted": r.discounted,
                "level_before_discount": r.level_before_discount,
                "empty": bool(r.discounted and (r.total_points or 0) < 1e-9),
                "yes_applied": r.yes_applied,
                "yes_blocked_reason": r.yes_blocked_reason,
                "notes": list(r.notes),
                "warnings": list(r.warnings),
                "elements": rows,
                "groups": [
                    {
                        "element": names.get(k, k),
                        "group": SUBMIN_GROUP_LABELS.get(g, g),
                        "points": v,
                    }
                    for k, d in r.group_points.items()
                    for g, v in d.items()
                ],
                "submins": [
                    {
                        "element": names.get(c.element, c.element),
                        "group": SUBMIN_GROUP_LABELS.get(c.group, c.group) if c.group else None,
                        "achieved": c.achieved,
                        "required": c.required,
                        "clause": c.clause,
                        "passed": c.passed,
                    }
                    for c in r.submin_checks
                ],
                "gender_gaps": gender_open_gaps(card, inp.indicators, s.fin(), s.draft)
                if card and not r.deemed
                else [],
                "tf_available": bool(
                    s.draft and any(i.group == "tf" for e in s.elements for i in e.indicators)
                ),
            }
        )
    )


def tf_routes(session: dict, budget: float | None = None) -> dict:
    """Draft Transformation Fund vs direct SD + ED planner (app.py tf_planner)."""
    s = _Session(session)
    esd = s.element("esd")
    if esd is None or not s.draft:
        return {"ok": False, "reason": "Draft rules and an ESD element are needed."}
    tf = next((i for i in esd.indicators if i.group == "tf"), None)
    if tf is None:
        return {"ok": False, "reason": "This scorecard has no Transformation Fund indicator."}
    sd = [i for i in esd.indicators if i.group == "sd" and not i.bonus and i.base == "npat"]
    ed = [i for i in esd.indicators if i.group == "ed" and not i.bonus and i.base == "npat"]
    npat = s.fin().npat
    if not npat or npat <= 0:
        return {
            "ok": False,
            "reason": "Enter a positive NPAT in the profile to compare the routes.",
        }
    if s.store["entry"].get("esd", "ind") != "ind":
        return {"ok": False, "reason": "The planner needs ESD entered as indicators (not points)."}
    hi = int(max(npat * 0.05, 10_000))
    b = int(npat * tf.target / 100) if budget is None else int(min(max(float(budget), 0), hi))
    drop = {i.clause for i in sd + ed} | {tf.clause}
    weights = [(i, i.target) for i in sd + ed]
    tot_w = sum(w for _, w in weights) or 1
    base = calculate(s.current_input())
    routes = []
    for name, ov in (
        ("Transformation Fund", {"drop": drop, "add": {tf.clause: Rand(float(b))}}),
        (
            "Direct SD + ED",
            {"drop": drop, "add": {i.clause: Rand(b * w / tot_w) for i, w in weights}},
        ),
    ):
        res = calculate(s.current_input(ov))
        routes.append(
            {
                "name": name,
                "esd_points": res.element_points.get("esd", 0.0),
                "total": res.total_points,
                "delta": (res.total_points or 0) - (base.total_points or 0),
                "level_label": res.level_label,
            }
        )
    return _clean(
        {
            "ok": True,
            "budget": b,
            "min": 0,
            "max": hi,
            "pct_of_npat": b / npat * 100,
            "routes": routes,
            "split_note": "SD + ED budget split in proportion to their NPAT targets "
            + ", ".join(f"{i.name} {num(i.target)}%" for i, _ in weights)
            + ".",
        }
    )


# ------------------------------------------------------------------ procurement calculator
def procurement_template() -> str:
    return template_csv()


def procurement_parse_csv(text: str) -> dict:
    """Uploaded supplier CSV -> table rows, or every problem found."""
    if len(text.encode("utf-8")) > MAX_SUPPLIER_CSV_BYTES:
        return {
            "ok": False,
            "errors": ["That file is over 2 MB. Split the supplier list or remove extra columns."],
        }
    suppliers, errs = proc_parse_csv(text)
    if errs:
        return {"ok": False, "errors": [str(e) for e in errs[:20]], "more": max(len(errs) - 20, 0)}
    return _clean({"ok": True, "records": [to_record(x) for x in suppliers]})


def procurement_summary(session: dict, element: str, records: list[dict]) -> dict:
    """Supplier rows -> TMPS and the % of TMPS per procurement indicator (Statement 400)."""
    s = _Session(session)
    el = s.element(element)
    if el is None:
        return {"ok": False}
    inds = procurement_indicators(el)
    suppliers, errs = proc_parse_rows(records)
    out: dict = {
        "ok": True,
        "errors": [str(e) for e in errs[:20]],
        "more_errors": max(len(errs) - 20, 0),
        "count": len(suppliers),
    }
    if not suppliers:
        return _clean(out)
    summary = summarise(suppliers)
    values, unmatched = summary.indicator_values(el)
    rows = []
    for ind in inds:
        if ind.clause not in values:
            continue
        pct = values[ind.clause]
        rows.append(
            {
                "indicator": ind.name,
                "recognised": _rand_text(pct * summary.tmps / 100),
                "pct": pct,
                "target": f"{num(ind.target)}%",
                "points": indicator_points(ind, pct, Financials(), s.draft),
                "max": ind.points,
            }
        )
    out.update(
        {
            "total_spend": summary.total_spend,
            "excluded": summary.excluded_total,
            "tmps": summary.tmps,
            "rows": rows,
            "notes": list(summary.notes),
            "unmatched": [i.name for i in unmatched],
            "apply": {clause: pct for clause, pct in values.items()},
            "csv": proc_to_csv(suppliers),
        }
    )
    return _clean(out)


# ------------------------------------------------------------------ contributions
def contribution_types(session: dict, element: str) -> dict:
    s = _Session(session)
    tg = contrib_targets(s.card, element) if s.card else None
    if not tg:
        return {"targets": [], "types": []}
    allowed = [
        label
        for _k, (label, _e, sed, rate) in CONTRIB_TYPES.items()
        if element != "sed" or (sed is not None and not rate)
    ]
    rate_types = [label for _k, (label, _e, _sed, rate) in CONTRIB_TYPES.items() if rate]
    return {"targets": [t.label for t in tg], "types": allowed, "rate_types": rate_types}


def contributions_summary(session: dict, element: str, records: list[dict]) -> dict:
    """Contribution lines valued at Annexe 400(B) / 500(A) benefit factors."""
    s = _Session(session)
    tg = contrib_targets(s.card, element) if s.card else None
    if not tg:
        return {"ok": False}
    lines, errs = parse_contributions(records, s.card, element)
    out: dict = {
        "ok": True,
        "errors": [str(e) for e in errs[:20]],
        "more_errors": max(len(errs) - 20, 0),
        "count": len(lines),
    }
    if not lines:
        return _clean(out)
    summary = summarise_contributions(lines, s.card)
    base = s.fin().npat
    mode = s.store["modes"].get(element, "pct")
    rows = []
    for t in tg:
        clause = t.indicator.clause
        if clause not in summary.by_clause:
            continue
        pct = summary.percent_of(clause, base)
        rows.append(
            {
                "indicator": t.label,
                "face": _rand_text(summary.gross_by_clause[clause]),
                "recognised": _rand_text(summary.by_clause[clause]),
                "pct": pct,
                "target": f"{num(t.indicator.target)}%",
                "points": None
                if pct is None
                else indicator_points(t.indicator, pct, Financials(), s.draft),
                "max": t.indicator.points,
            }
        )
    can_apply = mode == "rand" or bool(base and base > 0)
    out.update(
        {
            "rows": rows,
            "notes": list(summary.notes),
            "can_apply": can_apply,
            "apply": {
                clause: (rec if mode == "rand" else rec / base * 100)
                for clause, rec in summary.by_clause.items()
            }
            if can_apply
            else {},
        }
    )
    return _clean(out)


# ------------------------------------------------------------------ Net Value
def net_value(session: dict, element: str, box: dict) -> dict:
    """Annexe 100(E) Net Value from share values, debt and the graduation factor."""
    s = _Session(session)
    el = s.element(element)
    nv = next((i for i in el.indicators if i.group == "net_value"), None) if el else None
    if nv is None:
        return {"ok": False, "reason": "No Net Value indicator on this element."}
    entity = _num(box.get("entity_value")) or 0.0
    if not entity:
        return {"ok": False, "reason": "Enter the company's value to see the calculation."}
    try:
        year = measurement_year(
            _date(box.get("equity_date")) or date.today(),
            _date(box.get("measurement_date")) or date.today(),
        )
        res = calculate_net_value(
            NetValueInput(
                black_equity_value=_num(box.get("black_equity_value")) or 0.0,
                acquisition_debt=_num(box.get("acquisition_debt")) or 0.0,
                entity_value=entity,
                economic_interest_pct=_num(box.get("economic_interest_pct")) or 0.0,
                year=year,
                weighting=nv.points,
                target_pct=_num(box.get("target_pct")) or NV_TARGET,
            )
        )
    except ValueError as exc:
        return {"ok": False, "reason": f"Check these inputs: {exc}"}
    nvs = next((x for x in s.card.submins if x.group == "net_value"), None)
    return _clean(
        {
            "ok": True,
            "rows": [
                ["Year since equity interest date", f"{year}"],
                ["Graduation factor", f"{graduation_factor(year):.0%}"],
                ["Deemed value (shares less debt / company)", f"{res.deemed_value_pct:.2f}%"],
                ["Required this year (target × factor)", f"{res.required_pct:.2f}%"],
                ["Formula A points", f"{res.points_a:.2f}"],
                ["Formula B points", f"{res.points_b:.2f}"],
            ],
            "points": round(res.points, 2),
            "max": nv.points,
            "notes": list(res.notes),
            "below_submin": bool(nvs and res.points < nvs.required),
            "submin": nvs.required if nvs else None,
        }
    )


# ------------------------------------------------------------------ client files
def client_save(session: dict) -> dict:
    s = _Session(session)
    raw = client_file.dump(s.store, s.sector, s.draft)
    return {
        "text": raw.decode("utf-8"),
        "filename": client_file.filename(s.store["profile"].get("company", "")),
    }


def client_open(text: str) -> dict:
    """Parse a client file. Consent from the file is ignored (the caller keeps its own)."""
    try:
        store, app_meta, notes = client_file.parse(text.encode("utf-8"))
    except client_file.ClientFileError as exc:
        return {"ok": False, "problems": list(exc.problems)}
    return _clean({"ok": True, "store": store, "app": app_meta, "notes": notes[:10]})


# ------------------------------------------------------------------ gap report
def report(session: dict) -> dict:
    """Data for the printable gap report (same context the WeasyPrint PDF uses)."""
    s = _Session(session)
    sc = score(session)
    if not sc.get("ok"):
        return {"ok": False, "problems": sc.get("problems", [])}
    if sc["deemed"] or s.card is None:
        return {"ok": False, "problems": ["The gap report needs the full scorecard path."]}
    inp = s.current_input()
    r = calculate(inp)
    ctx = _report_context(
        r,
        s.card,
        s.store["profile"],
        s.label,
        s.cfg,
        draft=s.draft,
        company_name=s.store["profile"].get("company") or "Your company",
        indicators=inp.indicators,
        financials=inp.financials,
    )
    ctx["ok"] = True
    ctx["score"] = sc
    return _display(_clean(ctx))


# ------------------------------------------------------------------ worker entry point
_FUNCS = {
    "meta": meta,
    "fresh": fresh,
    "context": context,
    "problems": problems,
    "convert_mode": convert_mode,
    "score": score,
    "tf_routes": tf_routes,
    "procurement_template": procurement_template,
    "procurement_parse_csv": procurement_parse_csv,
    "procurement_summary": procurement_summary,
    "contribution_types": contribution_types,
    "contributions_summary": contributions_summary,
    "net_value": net_value,
    "client_save": client_save,
    "client_open": client_open,
    "report": report,
}


def call(name: str, args_json: str) -> str:
    """Dispatch one call from the browser. Errors come back as {"error": ...}, never raise."""
    fn = _FUNCS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown call: {name}"})
    try:
        args = json.loads(args_json) if args_json else []
        result = fn(*args) if isinstance(args, list) else fn(**args)
        return json.dumps(_clean(result), allow_nan=False)
    except Exception as exc:  # noqa: BLE001 - reported to the UI as a generic error
        return json.dumps({"error": type(exc).__name__, "detail": str(exc)[:300]})
