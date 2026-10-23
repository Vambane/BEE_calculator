"""WeasyPrint PDF gap report (design v1.2). Templates live under ``report/``."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from bee.levels import LEVELS
from bee.models import ScoreResult
from bee.rules import Scorecard
from bee.sectors.base import SectorConfig

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "report"


def _jinja_env() -> Environment:
    """Jinja env with HTML/XML autoescape on (XSS-safe company/user fields in PDF HTML)."""
    return Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml"]),
    )


def _next_level_gap(points: float) -> tuple[float, int] | None:
    for minimum, level, _ in reversed(LEVELS):
        if points < minimum - 1e-9:
            return round(minimum - points, 2), level
    return None


def _visible(el, draft: bool):
    return [i for i in el.indicators if draft or not i.draft_only]


def _elements(card: Scorecard, result: ScoreResult, draft: bool) -> list[dict]:
    failed = {c.element for c in result.submin_checks if not c.passed}
    out = []
    for e in card.elements:
        if e.max_points(draft=draft) <= 0:
            continue
        mx = e.max_points(draft=draft)
        if card.key.startswith("construction-qse"):
            mx += e.bonus_max or 0
        pts = result.element_points.get(e.key, 0.0)
        inds = _visible(e, draft)
        tips = [i for i in inds if not i.bonus][:3]
        out.append(
            dict(
                name=e.name,
                points=pts,
                max=mx,
                gap=max(mx - pts, 0.0),
                submin_failed=e.key in failed,
                explainer=(
                    f"{len(inds)} indicator(s) on this scorecard."
                    if inds
                    else "Points entered against the element weighting."
                ),
                target_text="; ".join(
                    f"{i.name} (target {i.target:g}, {i.points:g} pts)" for i in tips
                )
                or e.name,
                value_text=f"{pts:.1f} pts",
                rand_to_target="See the app's Where to gain points tab.",
                clause=", ".join(i.clause for i in tips) or e.key,
            )
        )
    return out


def _notes(result: ScoreResult) -> list[dict]:
    notes = []
    for n in result.notes:
        title, _, body = n.partition(":")
        if body:
            notes.append({"title": title.strip(), "body": body.strip(), "src": "bee engine"})
        else:
            notes.append({"title": "Note", "body": n, "src": "bee engine"})
    for w in result.warnings:
        notes.append({"title": "Warning", "body": w, "src": "sector config"})
    return notes


def _report_context(
    result: ScoreResult,
    card: Scorecard,
    profile: dict,
    scorecard_label: str,
    cfg: SectorConfig,
    *,
    draft: bool = False,
    company_name: str = "Your company",
    example: bool = False,
    indicators: dict | None = None,
    financials=None,
) -> dict:
    els = _elements(card, result, draft)
    from bee.models import Financials
    from bee_ui.core import gender_contribution, gender_open_gaps

    fin = financials if financials is not None else Financials()
    inds = indicators or {}
    gx, gy = gender_contribution(card, inds, fin, draft)
    gender_rows = gender_open_gaps(card, inds, fin, draft)
    # Enrich element detail with women lines (include zeros).
    by_el: dict[str, list] = {}
    for g in gender_rows:
        by_el.setdefault(g["element_name"], []).append(g)
    for e in els:
        rows = by_el.get(e["name"], [])
        if rows:
            e["gender_rows"] = rows
            e["explainer"] = (
                e["explainer"]
                + " Black women / Black female lines: "
                + "; ".join(f"{g['name']} {g['achieved']:g}/{g['max']:g} pts" for g in rows)
                + "."
            )
    gaps = sorted(
        [
            {"name": e["name"], "points": e["gap"], "tip": e["explainer"]}
            for e in els
            if e["gap"] > 0
        ],
        key=lambda g: -g["points"],
    )
    out_of = card.display_max(draft=draft)
    sector_note = None
    if cfg.status in ("not_loaded", "legacy"):
        sector_note = f"No verified {cfg.name} scorecard: Generic targets applied (fallback)."
    elif result.warnings:
        sector_note = result.warnings[0]
    if result.discounted:
        failed = [c for c in result.submin_checks if not c.passed]
        discount_reason = (
            "; ".join(
                f"{c.element}{('/' + c.group) if c.group else ''} {c.achieved:.1f}/{c.required:g}"
                for c in failed
            )
            or "priority-element sub-minimum missed"
        )
        discount_clause = failed[0].clause if failed else "S5 cl. 3.3.3.1"
    else:
        discount_reason, discount_clause = None, ""
    gap = None if result.level_points is None else _next_level_gap(result.level_points)
    return dict(
        example=example,
        prepared_date=date.today().strftime("%-d %b %Y"),
        scorecard_label=f"Scorecard: {scorecard_label}",
        sector_note=sector_note,
        company=dict(
            name=company_name or "Your company",
            size=str(result.size.value if hasattr(result.size, "value") else result.size),
            province="",
            sector_code=cfg.name,
        ),
        ruleset=dict(
            id="Amended Codes 2019 + QSE CS600 + gazetted sector codes",
            version="1.2",
        ),
        result=dict(
            level_label=result.level_label
            + (f" (was {result.level_before_discount})" if result.discounted else ""),
            total=result.total_points or 0.0,
            max_total=out_of,
            discount_applied=result.discounted,
            discount_reason=discount_reason,
            discount_clause=discount_clause,
            elements=els,
            gaps=gaps,
            next_level=f"{gap[0]:.1f} pts to Level {gap[1]}" if gap else None,
            gender_contribution=(
                f"Black women / Black female contribution: {gx:g} of {gy:g} pts" if gy > 0 else None
            ),
            gender_rows=gender_rows,
        ),
        scenario=None,
        notes=_notes(result),
        method_text=(
            "Each indicator scores min(actual / target, 1) × points, capped at the indicator "
            "weighting. Element-level sector cards accept pre-calculated points. Levels follow "
            "Statement 000 cl. 8.2.1 (or the sector's absolute table)."
        ),
        assumptions=[
            "Net Value is the figure from your verification agency; this tool does not "
            "calculate Annexe 100(E).",
            "QSE priority-element sub-minimums use 40% of the QSE weightings (interpretation).",
            "Draft Transformation Fund (when enabled) scores on the indicator sum "
            "(ESD 45 Fund / 40 ED+SD), not scaled to 55 — DRAFT, NOT IN FORCE.",
            "This report is a planning aid, not a SANAS verification certificate.",
        ],
    )


def render_report_html(
    result: ScoreResult,
    card: Scorecard | None,
    profile: dict,
    scorecard_label: str,
    cfg: SectorConfig,
    *,
    draft: bool = False,
    company_name: str = "Your company",
    example: bool = False,
    indicators: dict | None = None,
    financials=None,
) -> str:
    """Return the gap-report HTML string (autoescaped). Used by ``render_pdf`` and tests."""
    if card is None:
        raise ValueError("PDF requires a scored (non-EME-affidavit) scorecard")
    ctx = _report_context(
        result,
        card,
        profile,
        scorecard_label,
        cfg,
        draft=draft,
        company_name=company_name,
        example=example,
        indicators=indicators,
        financials=financials,
    )
    return _jinja_env().get_template("report_template.html").render(**ctx)


def render_pdf(
    result: ScoreResult,
    card: Scorecard | None,
    profile: dict,
    scorecard_label: str,
    cfg: SectorConfig,
    *,
    draft: bool = False,
    company_name: str = "Your company",
    example: bool = False,
    indicators: dict | None = None,
    financials=None,
) -> bytes:
    """Return PDF bytes for a scored result. Raises on WeasyPrint/template errors."""
    from weasyprint import HTML  # lazy: keeps app import light when PDF unused

    html = render_report_html(
        result,
        card,
        profile,
        scorecard_label,
        cfg,
        draft=draft,
        company_name=company_name,
        example=example,
        indicators=indicators,
        financials=financials,
    )
    return HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf()
