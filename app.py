"""BEE Check: thin Streamlit UI over the ``bee`` engine (design spec v1.1).

All scoring is done by ``bee.calculate``; this file only collects inputs, validates them and
renders results. No inputs are logged. Run: ``streamlit run app.py``.
"""

from __future__ import annotations

import logging
from dataclasses import replace as dc_replace
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bee import EnterpriseSize, Financials, Rand, calculate
from bee.contributions import COLUMNS as CONTRIB_COLUMNS
from bee.contributions import TYPES as CONTRIB_TYPES
from bee.contributions import parse_rows as parse_contributions
from bee.contributions import summarise as summarise_contributions
from bee.contributions import targets as contrib_targets
from bee.indicators import indicator_points
from bee.npat import resolve as resolve_npat
from bee.procurement import COLUMNS as PROC_COLUMNS
from bee.procurement import EXCLUSIONS as PROC_EXCLUSIONS
from bee.procurement import (
    LEVEL_OPTIONS,
    parse_csv,
    parse_rows,
    procurement_indicators,
    summarise,
    template_csv,
    to_record,
)
from bee.procurement import SIZES as PROC_SIZES
from bee.procurement import to_csv as to_proc_csv
from bee.registry import get_sector
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
    is_scenario_widget_key,
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

# Honey visual language (v1.3) — theme/CSS/Plotly only; no scoring changes.
INK, INK_MUTED = "#1A1A1A", "#4A4A4A"
PAPER_2, LINE = "#F3EDE0", "rgba(26,26,26,0.10)"
GOLD, GOLD_TINT = "#D4A017", "#F7ECD9"  # primary + gap / points-available
# Back-compat aliases used by the chart block
GREEN, OCHRE, OCHRE_TINT = INK, GOLD, GOLD_TINT  # achieved=charcoal; gap=gold
MODES = {"rand": "Rand amounts", "pct": "Percentages"}
ENTRY = {"ind": "Indicators", "pts": "Points (pre-calculated)"}
DRAFT_LABEL = "Draft 2026 rules (Transformation Fund)"
# Session-scoped abuse guards (Streamlit has no shared backend). Edge/WAF limits: DEFERRED.
MAX_PDF_UNLOCK_ATTEMPTS = 5
MAX_PDF_BUILDS = 5
MAX_CALCULATE_CALLS = 60  # per browser session

_REPO_ROOT = Path(__file__).resolve().parent
_PRIVACY_MD = _REPO_ROOT / "docs" / "PRIVACY.md"
_HOWTO_MD = _REPO_ROOT / "docs" / "HOW_TO.md"
# GitHub blob for docs/PRIVACY.md on main (stable after this PR merges).
PRIVACY_GITHUB = "https://github.com/Vambane/BEE_calculator/blob/main/docs/PRIVACY.md"
HOWTO_GITHUB = "https://github.com/Vambane/BEE_calculator/blob/main/docs/HOW_TO.md"
CONSENT_LABEL = (
    "I have read the privacy notice and agree to this processing for this session's scorecard."
)
# Compliance §1 short notice (privacy-notice-v1.md) — keep in sync with docs/PRIVACY.md.
PRIVACY_SHORT = (
    "**Privacy notice.** We use the company figures you enter only to calculate a B-BBEE "
    "scorecard for this session. Aggregates that relate to race or gender are special "
    "personal information under POPIA s26; we process them only for this scorecard. We do "
    "not ask for ID numbers or individual names.\n\n"
    "Your inputs are kept only for this interactive session on the app host and are "
    "discarded when the session ends. They are not written to a database or other "
    "long-term store. We do not put your inputs into analytics or error reports "
    "(usage statistics are off).\n\n"
    "[Privacy policy](?page=privacy) · [Full text on GitHub](" + PRIVACY_GITHUB + ")"
)

_log = logging.getLogger("bee_check")


def report_unexpected(exc: BaseException, *, what: str) -> None:
    """Support hint (time only, no PII) + log exception type to stderr for Cloud logs."""
    when = datetime.now(UTC).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    _log.warning("%s failed: %s", what, type(exc).__name__)
    st.caption(
        f"If this keeps happening, contact support and mention: {what} · {when} "
        "(no personal details needed)."
    )


def load_privacy_md() -> str:
    """Return docs/PRIVACY.md body, or a short fallback if the file is missing."""
    try:
        return _PRIVACY_MD.read_text(encoding="utf-8")
    except OSError:
        return f"Privacy policy file is unavailable in this build. See {PRIVACY_GITHUB}"


def load_howto_md() -> str:
    """Return docs/HOW_TO.md body, or a short fallback if the file is missing."""
    try:
        return _HOWTO_MD.read_text(encoding="utf-8")
    except OSError:
        return f"How to guide is unavailable in this build. See {HOWTO_GITHUB}"


def _clear_page_query() -> None:
    try:
        del st.query_params["page"]
    except KeyError:
        pass


def render_privacy_page() -> None:
    """In-app privacy page (?page=privacy). Multipage pages/ would pollute wizard sidebar."""
    st.title("Privacy policy")
    st.caption(
        "In-app path: `?page=privacy` (documented as `/privacy` until a public URL exists). "
        f"Canonical copy: [docs/PRIVACY.md]({PRIVACY_GITHUB})."
    )
    st.markdown(load_privacy_md())
    st.markdown(f"[How to use](?page=howto) · [Full text on GitHub]({PRIVACY_GITHUB})")
    if st.button("Back to calculator", type="primary"):
        _clear_page_query()
        st.rerun()


def render_howto_page() -> None:
    """In-app how-to page (?page=howto). Multipage pages/ would pollute wizard sidebar."""
    st.title("How to use")
    st.caption(
        "In-app path: `?page=howto` (documented as `/howto` until a public URL exists). "
        f"Canonical copy: [docs/HOW_TO.md]({HOWTO_GITHUB})."
    )
    st.markdown(load_howto_md())
    st.markdown(f"[Privacy policy](?page=privacy) · [Full text on GitHub]({HOWTO_GITHUB})")
    if st.button("Back to calculator", type="primary"):
        _clear_page_query()
        st.rerun()


st.set_page_config(page_title="BEE Check", layout="centered")
# UX-C1: st.html injects CSS/DOM; st.markdown(..., unsafe_allow_html=True) can print
# raw <style>/hex markup as visible text on Streamlit Cloud (Design mock UX-C1).
st.html(
    """
<style>
/* Honey visual language — light CSS; Streamlit theme owns most colours */
h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
  font-family: SourceSerif4, Georgia, serif !important;
  letter-spacing: -0.02em;
  font-weight: 500;
}
.block-container {
  padding-top: 1.5rem;
  padding-bottom: 4rem;
  max-width: 920px;
}
.stButton > button[kind="primary"],
.stDownloadButton > button {
  background: #D4A017 !important;
  color: #1A1A1A !important;
  border: none !important;
  border-radius: 999px !important;
  min-height: 48px;
  font-weight: 500;
}
.stButton > button[kind="primary"]:hover,
.stDownloadButton > button:hover {
  background: #B8860B !important;
  color: #1A1A1A !important;
}
.bee-hex-divider {
  height: 28px;
  margin: 1.5rem auto;
  width: 28px;
  background: #D4A017;
  opacity: 0.85;
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(212, 160, 23, 0.45) !important;
  box-shadow: 0 8px 24px rgba(26, 26, 26, 0.06);
}
/* UX-C3: custom theme fonts must not steal Material Symbols ligatures on expanders */
[data-testid="stExpanderIcon"],
[data-testid="stIconMaterial"],
[data-testid="stExpanderStepChevron"],
[data-testid="stExpanderStepIcon"] {
  font-family: "Material Symbols Rounded" !important;
  font-weight: 400 !important;
  font-style: normal !important;
  font-synthesis: none !important;
  letter-spacing: normal !important;
  text-transform: none !important;
  -webkit-font-feature-settings: "liga" !important;
  font-feature-settings: "liga" !important;
}
</style>
"""
)

Q = st.query_params
S = st.session_state
S.setdefault("sector", Q.get("sector", "generic"))
S.setdefault("draft", Q.get("draft", "0") == "1")
S.setdefault("default_mode", "pct" if Q.get("mode") == "pct" else "rand")
# Canonical store: widget state is dropped for unrendered steps, so values live here.
S.setdefault("store", fresh_store())
S.setdefault("max_step", 0)
store = S.store
# Dedicated info views: ?page=privacy / ?page=howto (pages/ multipage would pollute the wizard sidebar).
_page = str(Q.get("page", "")).lower()
if _page == "privacy":
    render_privacy_page()
    st.stop()
if _page == "howto":
    render_howto_page()
    st.stop()
if Q.get("demo") == "1" and not S.get("demo_seeded"):  # illustrative inputs for demos only
    S.demo_seeded = True
    # Do not auto-consent (M3): seed figures but require an explicit tick.
    store["profile"].update(
        company="Example Co (Pty) Ltd", revenue=120_000_000.0, black_ownership=40.0
    )
    store["fin"].update(
        npat=8_000_000.0, leviable_amount=30_000_000.0, tmps=60_000_000.0, employees=150.0
    )
if S.get("demo_seeded"):
    st.info("EXAMPLE DATA: illustrative inputs (Indicators on Ownership/MC), not a real company.")
# H1: ignore ?step= and force profile until POPIA consent is given.
if not store.get("consent"):
    S.step = 0
else:
    S.setdefault(
        "step",
        int(Q.get("step", 0)) if str(Q.get("step", "0")).isdigit() else 0,
    )
valid_sectors = dict(sector_choices())
if S.sector not in valid_sectors:
    S.sector = "generic"


def bind(key: str, current):
    """Seed session_state for a keyed widget. Do not also pass default=/value= (B12)."""
    if key not in S:
        S[key] = current
    return key


def fin_obj(effective: bool = True) -> Financials:
    """Profile financials. ``effective`` swaps in the deemed NPAT when Statement 400
    cl. 3.2.1 applies (for validation, rand/% conversion and planners); the engine gets the
    raw figures (``effective=False``) and applies the rule itself, with a results note."""
    f = store["fin"]
    fin = Financials(
        npat=f["npat"] or None,
        leviable_amount=f["leviable_amount"] or None,
        tmps=f["tmps"] or None,
        employees=f["employees"] or None,
        npat_avg_5y=f.get("npat_avg_5y"),
        industry_norm_margin_pct=f.get("industry_norm_margin_pct") or None,
        qualifying_margin_pct=f.get("qualifying_margin_pct") or None,
    )
    if not effective:
        return fin
    basis = npat_basis_for(fin)
    if basis is None or not basis.deemed:
        return fin
    return dc_replace(fin, npat=basis.npat)


def npat_basis_for(fin: Financials):
    """cl. 3.2.1 basis for the profile, or None if the inputs are invalid."""
    try:
        return resolve_npat(
            float(store["profile"].get("revenue") or 0.0),
            fin.npat,
            fin.npat_avg_5y,
            fin.industry_norm_margin_pct,
            fin.qualifying_margin_pct,
        )
    except ValueError:
        return None


def context():
    cfg = get_sector(S.sector)
    variant = store["profile"]["variant"] if cfg.variants else None
    if variant not in (cfg.variants or (None,)):
        variant = cfg.default_variant
    # Invalid revenue (e.g. -1) must not crash the shell: size falls back for UI layout
    # only; validate() / footer(problems) still block Continue (Security M3 / Batch1).
    try:
        size = size_for(cfg, store["profile"]["revenue"], variant)
    except ValueError:
        size = EnterpriseSize.EME
    # UX-C2: EME affidavit hides the element card, but opt_scored must surface the QSE
    # scorecard steps (engine already remaps EME → QSE via SectorConfig.card).
    opt_scored = bool(store["profile"].get("opt_scored"))
    card = card_for(cfg, size, variant) if (size.value != "EME" or opt_scored) else None
    return cfg, variant, size, card


cfg, variant, size, card = context()
if S.get("demo_seeded") and card and not store.get("_demo_entries_done"):
    store["_demo_entries_done"] = True
    for e in card.elements:
        mode = default_entry_mode(e)
        store["entry"][e.key] = mode
        if mode == "ind" and e.indicators:
            # Illustrative percentages (~60% of each target) so gender lines are visible.
            pct_bucket = store["values"]["pct"].setdefault(e.key, {})
            for i in e.indicators:
                if i.group == "net_value" or i.base == "bool" or i.draft_only:
                    continue
                pct_bucket.setdefault(i.clause, round(0.6 * min(i.target, 100.0), 2))
        else:
            gs = [g for g in e.groups() if g != "tf"]
            if e.total is not None and sum(dict(e.group_max).values()) >= e.total:
                gs = [g for g in gs if g != "main"]
            store["points"][e.key] = {
                g: round(0.6 * e.max_points(g), 1) for g in gs if e.max_points(g) > 0
            }
elements = [e for e in card.elements if e.max_points() > 0] if card else []  # hide 0-max elements
steps = ["Profile", *[e.name for e in elements], "Results"]
S.step = min(S.step, len(steps) - 1)
# Reachable sidebar targets: Profile + steps already opened (incl. Results once visited).
S.max_step = min(max(S.get("max_step", 0), S.step), len(steps) - 1)
label = scorecard_label(cfg, size, variant)


def badge_line():
    st.markdown(f"**Scorecard: {label}**")
    if cfg.status == "verified" and cfg.key != "generic":
        st.markdown(":green-badge[Verified sector code]")
        if cfg.key in ("construction", "tourism", "ict") and card:
            st.caption(
                f"Scorecard total: out of {scorecard_max(card, S.draft):g}"
                + (" (draft ESD indicator sum)" if S.draft else "")
                + "."
            )
    elif cfg.status == "unverified":
        st.markdown(":orange-badge[Pending expert verification]")
        st.warning("This sector scorecard is not yet verified; treat results as indicative.")
    elif cfg.status in ("not_loaded", "legacy"):
        st.warning(
            f"No verified {cfg.name} scorecard in this version: Generic targets are applied "
            "(fallback)."
        )


def require_consent():
    """H1: refuse any non-profile / calculate path without an explicit consent tick."""
    if not store.get("consent"):
        S.step = 0
        st.rerun()


def go_to(n: int):
    """Navigate to step n. Consent gate; does not clear inputs (Design: navigate-only)."""
    if not S.store.get("consent"):
        S.step = 0
        return
    S.step = n
    S.max_step = max(S.get("max_step", 0), n)


def start_over():
    """Clear scenario store + PDF unlock + widget keys; return to Profile.

    Keeps draft toggle and default_mode (ruleset / entry prefs, not company data).
    Sector stays as-is so the picker does not jump; profile/variant reset inside store.
    """
    S.store = fresh_store()
    S.step = 0
    S.max_step = 0
    S.pop("demo_seeded", None)
    for k in list(S.keys()):
        if is_scenario_widget_key(k):
            del S[k]


def footer(problems_fn=None):
    err_key = f"_step_errs_{S.step}"
    if S.get(err_key):
        st.error("Please fix:\n\n" + "\n".join(f"- {p}" for p in S[err_key]))
    a, b = st.columns(2)
    if S.step > 0:
        a.button("Back", width="stretch", on_click=go_to, args=(S.step - 1,))
    if S.step < len(steps) - 1:
        nxt = steps[S.step + 1]
        if b.button(f"Continue to {nxt}", type="primary", width="stretch"):
            probs = problems_fn() if problems_fn else []
            if probs:
                S[err_key] = probs
                st.rerun()
            else:
                S.pop(err_key, None)
                go_to(S.step + 1)
                st.rerun()


# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("**BEE Check**")
    st.caption(f"{store['profile']['company'] or 'Your company'}  \n{label}")
    consented = bool(store.get("consent"))
    max_reached = S.get("max_step", 0)
    for i, s in enumerate(steps):
        if i == S.step:
            st.markdown(f"**→ {s}**")
        elif consented and i <= max_reached:
            # Navigate-only: preserve inputs; same go_to as Back/Continue.
            prefix = "✓ " if i < S.step else "○ "
            st.button(
                prefix + s,
                key=f"nav_step_{i}",
                on_click=go_to,
                args=(i,),
                width="stretch",
            )
        else:
            st.markdown(("✓ " if i < S.step else "○ ") + s)
    st.button(
        "Start over",
        key="start_over",
        on_click=start_over,
        width="stretch",
        help="Clear company inputs and PDF unlock, then return to Profile.",
    )
    st.divider()
    S.draft = st.toggle(
        DRAFT_LABEL,
        value=S.draft,
        help="Draft Statement 400 / draft QSE Code Series 600 of 2026 (GG 54032). NOT IN "
        "FORCE. Off by default.",
    )
    st.caption(
        "Ruleset: Amended Codes 2019, QSE CS600 (2015) and gazetted sector codes. Planning "
        "tool, not a verification certificate."
    )
    st.markdown("[How to use](?page=howto) · [Privacy policy](?page=privacy)")

st.progress((S.step + 1) / len(steps), text=f"Step {S.step + 1} of {len(steps)} · {steps[S.step]}")
if S.draft:
    st.warning(
        "DRAFT, NOT IN FORCE. Draft Statement 400 / Draft QSE Code Series 600 of 2026 "
        "(GG 54032, 29 Jan 2026). Transformation Fund uses indicator sums only "
        "(ESD max 45 Fund / 40 ED+SD); not scaled to 55."
    )


# ------------------------------------------------------------------ step 0: profile
def profile_step():
    st.title("Tell us about your company")
    st.caption(
        "B-BBEE scorecard, calmly estimated. Enter what you know — we'll show the level, "
        "the gaps, and what moves the needle."
    )
    st.markdown("New here? [How to use this calculator](?page=howto).")
    with st.container(border=True):
        st.markdown(PRIVACY_SHORT)
        with st.expander("Full privacy notice"):
            st.markdown(load_privacy_md())
        store["consent"] = st.checkbox(
            CONSENT_LABEL,
            value=store["consent"],
        )
    consented = bool(store["consent"])
    # UX-M1: clear stale "Tick the privacy consent box" once consent is ticked.
    if consented:
        err_key = f"_step_errs_{S.step}"
        errs = list(S.get(err_key) or [])
        cleaned = [e for e in errs if "consent" not in e.lower()]
        if cleaned != errs:
            if cleaned:
                S[err_key] = cleaned
            else:
                S.pop(err_key, None)
    p = store["profile"]
    with st.container(border=True):
        if not consented:
            st.caption("Tick the privacy consent box above to unlock company and financial fields.")
        p["company"] = st.text_input(
            "Company name (optional)", p["company"], max_chars=120, disabled=not consented
        )
        keys = list(valid_sectors)
        S.sector = st.selectbox(
            "Sector code",
            keys,
            index=keys.index(S.sector),
            format_func=lambda k: valid_sectors[k],
            help="Pick the sector code your business is measured under. If unsure, keep Generic.",
            disabled=not consented,
        )
        c = get_sector(S.sector)
        if c.variants:
            v = p["variant"] if p["variant"] in c.variants else c.default_variant
            p["variant"] = st.selectbox(
                "Scorecard variant",
                list(c.variants),
                index=list(c.variants).index(v),
                format_func=lambda s: s.replace("_", " ").title(),
                disabled=not consented,
            )
        # No min/max on BO/revenue (F-EDGE-OVER100 / Security M3): Streamlit's range
        # clamp keeps out-of-range keystrokes out of session_state, so Continue would
        # validate the *stale* prior value while the UI still shows a red range error.
        # Accept the typed value and fail-closed in validate() / footer(problems).
        # MBC-BUG-01: use bind()+key (no value=) so Enter/blur commits into session_state
        # and store in the same run — value= alone flaps / lags Size by one rerun.
        rev_k = bind("profile_revenue", float(p["revenue"] or 0.0))
        p["revenue"] = float(
            st.number_input(
                "Total revenue, last financial year (R)",
                step=1.0,
                format="%.0f",
                key=rev_k,
                disabled=not consented,
            )
        )
        bo_k = bind("profile_black_ownership", float(p["black_ownership"] or 0.0))
        p["black_ownership"] = float(
            st.number_input(
                "Black ownership (%)",
                step=1.0,
                key=bo_k,
                disabled=not consented,
                help="Voting rights / economic interest, 0–100% (GG 36928 Statement 100).",
            )
        )
        cfg2, _, size2, _ = context()
        st.caption(f":green-badge[Size: {cfg2.size_labels.get(size2, size2.value)}]")
        st.markdown(
            f"**Scorecard: {scorecard_label(cfg2, size2, p['variant'] if cfg2.variants else None)}**"
        )
        # Size drives steps/sidebar from the top-of-script context(); if revenue just
        # crossed a threshold, rerun once so badge/steps match the committed value.
        if size2 != size:
            st.rerun()
        f = store["fin"]
        a, b = st.columns(2)
        lev_k = bind("fin_leviable_amount", float(f["leviable_amount"] or 0.0))
        f["leviable_amount"] = float(
            a.number_input(
                "Leviable payroll (R)",
                step=1.0,
                format="%.0f",
                key=lev_k,
                disabled=not consented,
            )
        )
        npat_k = bind("fin_npat", float(f["npat"] or 0.0))
        f["npat"] = float(
            b.number_input(
                "Net profit after tax (R)",
                step=1.0,
                format="%.0f",
                key=npat_k,
                disabled=not consented,
            )
        )
        low_profit_inputs(f, consented)
        a, b = st.columns(2)
        tmps_k = bind("fin_tmps", float(f["tmps"] or 0.0))
        f["tmps"] = float(
            a.number_input(
                "Total measured procurement spend (R)",
                step=1.0,
                format="%.0f",
                key=tmps_k,
                disabled=not consented,
            )
        )
        emp_k = bind("fin_employees", float(f["employees"] or 0.0))
        f["employees"] = float(
            b.number_input(
                "Headcount (employees)",
                step=1.0,
                format="%.0f",
                key=emp_k,
                disabled=not consented,
            )
        )
        st.caption("These bases are captured once and used when you enter rand amounts later.")
        p["opt_scored"] = st.checkbox(
            "Score on the full scorecard even if a deemed (affidavit) level applies",
            value=p["opt_scored"],
            disabled=not consented,
        )
    with st.expander("YES Initiative (optional)"):
        tiers = ["none", "target", "1.5x", "2x"]
        p["yes_tier"] = st.selectbox(
            "YES tier achieved", tiers, index=tiers.index(p["yes_tier"]), disabled=not consented
        )
        prev = st.selectbox(
            "Previous B-BBEE level (needed for YES)",
            [None, *range(1, 9)],
            index=[None, *range(1, 9)].index(p["yes_prev_level"]),
            disabled=not consented,
        )
        p["yes_prev_level"] = prev
    if S.sector == "financial":
        with st.expander("Financial Services options (interpretations)"):
            o = store["options"]
            o["fs_skills_submin"] = st.radio(
                "Skills sub-minimum (cl. 3.3.1(b))",
                [8.0, 6.0],
                index=[8.0, 6.0].index(o.get("fs_skills_submin", 8.0)),
                format_func=lambda x: (
                    f"{x:g} points"
                    + (" (40% of 20, default)" if x == 8 else " (40% of 15, as printed)")
                ),
                disabled=not consented,
            )
            o["fs_rescale_109"] = st.checkbox(
                "Normalise Large scorecards to 109 before the level table",
                value=o.get("fs_rescale_109", True),
                disabled=not consented,
            )

    def problems():
        out = [] if store["consent"] else ["Tick the privacy consent box to continue."]
        cfg_, _, size_, card_ = context()
        # F-EDGE-OVER100: EME deemed hides the scorecard (card_=None) so element steps are
        # not shown, but profile BO/revenue must still gate Continue. Use the underlying
        # card when present; otherwise validate(profile) with card=None.
        val_card = card_
        if val_card is None and cfg_.cards:
            val_card = card_for(cfg_, size_, store["profile"].get("variant"))
        out += [p.message for p in validate(val_card, store["profile"], fin_obj(), {}, {}, {})]
        return out

    footer(problems)


# ------------------------------------------------------------------ low profit (cl. 3.2.1)
def low_profit_inputs(f: dict, consented: bool) -> None:
    """Statement 400 cl. 3.2.1: Turnover basis for NPAT-linked targets on a loss or low margin."""
    given = any(f.get(k) for k in ("industry_norm_margin_pct", "qualifying_margin_pct")) or (
        f.get("npat_avg_5y") is not None
    )
    with st.expander(
        "Loss or low profit? NPAT targets on a Turnover basis (cl. 3.2.1)",
        expanded=bool(given or (f["npat"] or 0) < 0),
    ):
        st.caption(
            "SD, ED and SED targets are a % of NPAT. If there was no profit last year or on "
            "average over five years, or the margin is below a quarter of the industry norm, "
            "they are set on Turnover x an Indicative Profit Margin instead. Industry norms "
            "are published by Stats SA."
        )
        a, b, c = st.columns(3)
        k = bind("fin_npat_avg_5y", f.get("npat_avg_5y"))
        f["npat_avg_5y"] = a.number_input(
            "5-year average NPAT (R)",
            value=None,
            step=1.0,
            format="%.0f",
            key=k,
            disabled=not consented,
            help="Optional. Leave blank if you only have last year's NPAT.",
        )
        k = bind("fin_industry_norm", f.get("industry_norm_margin_pct"))
        f["industry_norm_margin_pct"] = b.number_input(
            "Industry norm margin (%)",
            value=None,
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key=k,
            disabled=not consented,
            help="The industry's net profit margin norm (Stats SA).",
        )
        k = bind("fin_qualifying_margin", f.get("qualifying_margin_pct"))
        f["qualifying_margin_pct"] = c.number_input(
            "Qualifying year margin (%)",
            value=None,
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            key=k,
            disabled=not consented,
            help="NPAT / Turnover of the most recent year in which the margin was at least a "
            "quarter of the industry norm.",
        )
        raw = fin_obj(effective=False)
        try:
            basis = resolve_npat(
                float(store["profile"].get("revenue") or 0.0),
                raw.npat,
                raw.npat_avg_5y,
                raw.industry_norm_margin_pct,
                raw.qualifying_margin_pct,
            )
        except ValueError as exc:
            st.error(str(exc))
            return
        if not basis.deemed:
            st.caption("NPAT basis applies: targets use last year's NPAT.")
        elif basis.npat is None:
            st.warning(f"Turnover basis applies ({'; '.join(basis.reasons)}). {basis.problem}")
        else:
            st.info(basis.note(float(store["profile"].get("revenue") or 0.0)))


# ------------------------------------------------------------------ benefit factors
def contributions_panel(el, mode: str, vals: dict) -> None:
    """ED / SD / SED contribution lines valued at Annexe 400(B) / 500(A) benefit factors."""
    tg = contrib_targets(card, el.key)
    if not tg:
        return
    box = store.setdefault("contributions", {}).setdefault(
        el.key, {"records": [], "version": 0, "current": None}
    )
    with st.expander(
        "Value contributions with benefit factors", expanded=bool(box["current"] or box["records"])
    ):
        st.caption(
            "List each contribution at face value and pick its type. The app applies the "
            "gazetted benefit factor (e.g. an interest-free loan counts at 70%, a guarantee at "
            "50%, staff time at 60%) and totals the recognised value per indicator."
        )
        ek = f"contrib_editor_{el.key}_{box['version']}"
        if ek not in S and box.get("current") is not None:
            box["records"] = box["current"]
        cols = [label for _, label in CONTRIB_COLUMNS]
        frame = pd.DataFrame(box["records"], columns=cols)
        for c in ("Amount (R)", "Prime / ordinary rate %", "Actual rate %"):
            frame[c] = pd.to_numeric(frame[c], errors="coerce").astype("float64")
        for c in ("Beneficiary", "Counts towards", "Contribution type"):
            frame[c] = frame[c].astype("object")
        allowed = [
            label
            for k, (label, _e, sed, rate) in CONTRIB_TYPES.items()
            if el.key != "sed" or (sed is not None and not rate)
        ]
        edited = st.data_editor(
            frame,
            key=ek,
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "Beneficiary": st.column_config.TextColumn(),
                "Counts towards": st.column_config.SelectboxColumn(
                    options=[t.label for t in tg], required=True
                ),
                "Contribution type": st.column_config.SelectboxColumn(
                    options=allowed, required=True
                ),
                "Amount (R)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                "Prime / ordinary rate %": st.column_config.NumberColumn(
                    min_value=0.0,
                    max_value=100.0,
                    help="Lower-interest loans: prime rate. Lower-dividend investments: the "
                    "ordinary shareholders' dividend rate.",
                ),
                "Actual rate %": st.column_config.NumberColumn(
                    min_value=0.0, max_value=100.0, help="The rate actually charged or paid"
                ),
            },
        )
        box["current"] = edited.to_dict("records")
        lines, errs = parse_contributions(box["current"], card, el.key)
        if errs:
            st.warning(
                "Fix these lines to include them:\n\n"
                + "\n".join(f"- {e}" for e in errs[:20])
                + ("\n- ..." if len(errs) > 20 else "")
            )
        if not lines:
            st.caption("Add contribution lines above to see their recognised value.")
            return
        summary = summarise_contributions(lines, card)
        base = fin_obj().npat
        rows = []
        for t in tg:
            if t.indicator.clause not in summary.by_clause:
                continue
            rec = summary.by_clause[t.indicator.clause]
            pct = summary.percent_of(t.indicator.clause, base)
            rows.append(
                {
                    "Indicator": t.label,
                    "Face value": _rand(summary.gross_by_clause[t.indicator.clause]),
                    "Recognised": _rand(rec),
                    "% of NPAT": "enter NPAT" if pct is None else f"{pct:.2f}%",
                    "Target": f"{t.indicator.target:g}%",
                    "Points": "-"
                    if pct is None
                    else f"{indicator_points(t.indicator, pct, Financials(), S.draft):.2f} "
                    f"of {t.indicator.points:g}",
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        for n in summary.notes:
            st.caption(n)
        st.caption(
            "Shorter payment periods to SD beneficiaries use a separate formula: add them to "
            "the Supplier Development figure by hand."
        )
        can_apply = mode == "rand" or bool(base and base > 0)
        if not can_apply:
            st.caption("Enter a positive NPAT (or the Turnover basis) in the Profile to apply.")
        if st.button(
            "Use these values",
            type="primary",
            key=f"contrib_apply_{el.key}",
            disabled=not can_apply,
        ):
            for clause, rec in summary.by_clause.items():
                vals[clause] = rec if mode == "rand" else rec / base * 100
                S.pop(f"v_{mode}_{clause}", None)
            S[f"contrib_applied_{el.key}"] = True
            st.rerun()
        if S.pop(f"contrib_applied_{el.key}", None):
            st.success("Applied: recognised contribution values filled in below.")


def _rand(x: float) -> str:
    return f"R{x:,.0f}".replace(",", " ")


# ------------------------------------------------------------------ procurement calculator
MAX_SUPPLIER_CSV_BYTES = 2_000_000


def _decode_csv(raw: bytes) -> str:
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")  # Excel "CSV" on Windows


_PROC_DTYPES = {
    "Supplier": "object",
    "Spend (R)": "float64",
    "B-BBEE level": "object",
    "Size": "object",
    "Black ownership %": "float64",
    "Black women ownership %": "float64",
    "Designated group": "bool",
    "Empowering supplier": "bool",
    "1.2x multiplier": "bool",
    "TMPS exclusion": "object",
}


def _supplier_frame(records: list[dict]) -> pd.DataFrame:
    """Editor frame with fixed column types (an empty list would otherwise be all-float)."""
    cols = [label for _, label in PROC_COLUMNS]
    frame = pd.DataFrame(records, columns=cols)
    for col in ("Designated group", "Empowering supplier", "1.2x multiplier"):
        frame[col] = [v is True or (isinstance(v, bool) and v) for v in frame[col]]
    for col in ("Spend (R)", "Black ownership %", "Black women ownership %"):
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame.astype(_PROC_DTYPES)


def procurement_panel(el, mode: str, vals: dict) -> None:
    """Supplier list -> TMPS and the % of TMPS for each procurement indicator (Statement 400).

    The list lives in ``store['procurement']`` (session only). "Use these figures" writes the
    matched indicator values and sets TMPS in the profile; nothing is applied silently.
    """
    inds = procurement_indicators(el)
    if not inds:
        return
    proc = store.setdefault("procurement", {"records": [], "version": 0})
    with st.expander("Calculate procurement from a supplier list", expanded=bool(proc["records"])):
        st.caption(
            "List every supplier you paid in the measurement year with their B-BBEE level, "
            "size and ownership from their certificate or affidavit. The app works out TMPS "
            "and the recognised spend for each procurement indicator below. Only Empowering "
            "Suppliers count; suppliers with no certificate count at 0%."
        )
        c1, c2 = st.columns(2)
        c1.download_button(
            "Download template (CSV)",
            template_csv(),
            file_name="supplier-list-template.csv",
            mime="text/csv",
            key="proc_template",
            width="stretch",
        )
        up = c2.file_uploader(
            "Upload supplier list (CSV)",
            type=["csv"],
            key=f"proc_upload_{proc['version']}",
            label_visibility="collapsed",
            help="CSV in the template's format, up to 2 MB",
        )
        c2.caption("CSV in the template's format, up to 2 MB.")
        if up is not None:
            raw = up.getvalue()
            if len(raw) > MAX_SUPPLIER_CSV_BYTES:
                st.error("That file is over 2 MB. Split the supplier list or remove extra columns.")
            else:
                suppliers, errs = parse_csv(_decode_csv(raw))
                if errs:
                    st.error(
                        f"{len(errs)} problem(s) in the file. Fix them and upload again:\n\n"
                        + "\n".join(f"- {e}" for e in errs[:20])
                        + ("\n- ..." if len(errs) > 20 else "")
                    )
                else:
                    proc["records"] = [to_record(s) for s in suppliers]
                    proc["current"] = None
                    proc["version"] += 1  # fresh editor + uploader
                    st.rerun()

        ek = f"proc_editor_{proc['version']}"
        if ek not in S and proc.get("current") is not None:
            # Widget state is dropped when the step is left: rebuild from the last edits.
            proc["records"] = proc["current"]
        frame = _supplier_frame(proc["records"])
        edited = st.data_editor(
            frame,
            key=ek,
            num_rows="dynamic",
            hide_index=True,
            width="stretch",
            column_config={
                "Supplier": st.column_config.TextColumn(required=True),
                "Spend (R)": st.column_config.NumberColumn(min_value=0.0, format="%.2f"),
                "B-BBEE level": st.column_config.SelectboxColumn(
                    options=list(LEVEL_OPTIONS), help="1 to 8, or NC for no certificate"
                ),
                "Size": st.column_config.SelectboxColumn(options=list(PROC_SIZES)),
                "Black ownership %": st.column_config.NumberColumn(min_value=0.0, max_value=100.0),
                "Black women ownership %": st.column_config.NumberColumn(
                    min_value=0.0, max_value=100.0
                ),
                "Designated group": st.column_config.CheckboxColumn(
                    help="At least 51% owned by black designated groups (youth, people with "
                    "disabilities, unemployed, rural, military veterans)"
                ),
                "Empowering supplier": st.column_config.CheckboxColumn(
                    help="As stated on the supplier's certificate or affidavit. EMEs are "
                    "always Empowering Suppliers (cl. 3.3.4)."
                ),
                "1.2x multiplier": st.column_config.CheckboxColumn(
                    help="Statement 400 cl. 3.5: a Supplier Development beneficiary or "
                    "black-owned QSE/EME with a 3-year contract, or a supplier at least 51% "
                    "black owned or black women owned (flow-through)"
                ),
                "TMPS exclusion": st.column_config.SelectboxColumn(
                    options=list(PROC_EXCLUSIONS.values()),
                    help="Leave as 'Included in TMPS' unless the spend is excluded",
                ),
            },
        )
        proc["current"] = edited.to_dict("records")
        suppliers, errs = parse_rows(proc["current"])
        if errs:
            st.warning(
                "Fix these rows to include them:\n\n"
                + "\n".join(f"- {e}" for e in errs[:20])
                + ("\n- ..." if len(errs) > 20 else "")
            )
        if not suppliers:
            st.caption("Add suppliers above or upload the template to see the calculation.")
            return
        summary = summarise(suppliers)
        m1, m2, m3 = st.columns(3)
        m1.metric("Total spend", f"R{summary.total_spend:,.0f}".replace(",", " "))
        m2.metric("Excluded", f"R{summary.excluded_total:,.0f}".replace(",", " "))
        m3.metric("TMPS", f"R{summary.tmps:,.0f}".replace(",", " "))
        values, unmatched = summary.indicator_values(el)
        rows = []
        for ind in inds:
            if ind.clause not in values:
                continue
            pct = values[ind.clause]
            rows.append(
                {
                    "Indicator": ind.name,
                    "Recognised spend": f"R{pct * summary.tmps / 100:,.0f}".replace(",", " "),
                    "% of TMPS": f"{pct:.2f}%",
                    "Target": f"{ind.target:g}%",
                    "Points": f"{indicator_points(ind, pct, Financials(), S.draft):.2f} "
                    f"of {ind.points:g}",
                }
            )
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        for n in summary.notes:
            st.caption(n)
        if unmatched:
            st.caption(
                "Enter by hand (not measurable from the list): "
                + "; ".join(i.name for i in unmatched)
            )
        st.caption(
            "Recognised spend = spend x the supplier's recognition % (Level 1 135% ... "
            "Level 8 10%), x 1.2 where ticked (cl. 3.5). Planning estimate: confirm "
            "exclusions, multipliers and supplier evidence with your verification agency."
        )
        b1, b2 = st.columns(2)
        b2.download_button(
            "Download this list (CSV)",
            to_proc_csv(suppliers),
            file_name="supplier-list.csv",
            mime="text/csv",
            key="proc_export",
            width="stretch",
        )
        if b1.button(
            "Use these figures",
            type="primary",
            key="proc_apply",
            disabled=summary.tmps <= 0,
            width="stretch",
        ):
            store["fin"]["tmps"] = float(summary.tmps)
            S["fin_tmps"] = float(summary.tmps)
            for clause, pct in values.items():
                vals[clause] = pct * summary.tmps / 100 if mode == "rand" else pct
                S.pop(f"v_{mode}_{clause}", None)
            S["proc_applied"] = len(values)
            st.rerun()
        if S.pop("proc_applied", None):
            st.success(
                "Applied: TMPS set in your profile and the procurement indicators below "
                "filled from the supplier list."
            )


# ------------------------------------------------------------------ element steps
def element_step(el):
    require_consent()
    st.title(el.name)
    draft = S.draft
    opts = entry_options(el)
    ent = store["entry"].get(el.key, default_entry_mode(el))
    if len(opts) > 1:
        ek = bind(f"entry_{el.key}", ent)
        ent = st.segmented_control("Enter", opts, format_func=ENTRY.get, key=ek) or S[ek]
    store["entry"][el.key] = ent
    fin = fin_obj()
    if ent == "pts":
        pts = store["points"].setdefault(el.key, {})
        with st.container(border=True):
            st.caption("Enter points from your verification agency or consultant.")
            covered = el.total is not None and sum(dict(el.group_max).values()) >= el.total
            groups = [
                g
                for g in el.groups()
                if (draft or g != "tf")
                and not (g == "main" and covered)
                and el.max_points(g, draft) > 0
            ]
            for g in groups:
                mx = el.max_points(g, draft)
                pk = f"pt_{el.key}_{g}"
                bind(pk, float(pts.get(g, 0.0)))
                pts[g] = st.number_input(
                    f"{'Points' if g == 'main' else g.replace('_', ' ').title() + ' points'} (max {mx:g})",
                    min_value=0.0,
                    max_value=float(mx),
                    step=0.5,
                    key=pk,
                )
            bmax = (
                el.bonus_max
                if el.bonus_max is not None
                else sum(i.points for i in el.indicators if i.bonus)
            )
            if bmax:
                bk = f"pt_{el.key}_bonus"
                bind(bk, float(pts.get("bonus", 0.0)))
                pts["bonus"] = st.number_input(
                    f"Bonus points (max {bmax:g})",
                    min_value=0.0,
                    max_value=float(bmax),
                    step=0.5,
                    key=bk,
                )
    else:
        can_rand = el.key not in PCT_ONLY_ELEMENTS and any(
            rand_capable(el, i) for i in el.indicators
        )
        mode = store["modes"].get(el.key, S.default_mode if can_rand else "pct")
        if can_rand:
            mk = bind(f"mode_{el.key}", mode)
            new = (
                st.segmented_control("Enter as", list(MODES), format_func=MODES.get, key=mk)
                or S[mk]
            )
            if new != mode:  # convert entered values through the profile base
                src = store["values"][mode].get(el.key, {})
                dst = store["values"][new].setdefault(el.key, {})
                for i in el.indicators:
                    if (
                        i.clause in src
                        and rand_capable(el, i)
                        and not isinstance(src[i.clause], bool)
                    ):
                        base = getattr(fin, BASE_FIN[i.base])
                        dst[i.clause] = (to_rand if new == "rand" else to_pct)(src[i.clause], base)
                        S.pop(f"v_{new}_{i.clause}", None)
                mode = new
        else:
            mode = "pct"
        store["modes"][el.key] = mode
        vals = store["values"][mode].setdefault(el.key, {})
        procurement_panel(el, mode, vals)
        contributions_panel(el, mode, vals)
        nv = next((i for i in el.indicators if i.group == "net_value"), None)
        if nv is not None:
            with st.container(border=True):
                st.markdown("**Net Value**")
                cur = float(vals.get(nv.clause, 0.0) or 0.0) * nv.points / 100
                nvk = f"nv_{mode}_{el.key}"
                bind(nvk, cur)
                got = st.number_input(
                    f"Net Value points (0 to {nv.points:g}), from your verification agency",
                    min_value=0.0,
                    max_value=float(nv.points),
                    step=0.1,
                    key=nvk,
                    help="Net Value uses the Annexe 100(E) formula on share values and debt. "
                    "This version does not calculate it; use your verification agency's figure.",
                )
                vals[nv.clause] = got / nv.points * 100  # engine input: % of target achieved
                nvs = next((s for s in card.submins if s.group == "net_value"), None)
                st.caption(
                    (f"Sub-minimum {nvs.required:g} of {nv.points:g}. " if nvs else "")
                    + "No figure yet? Leave 0 and Ownership is flagged as at risk."
                )
        if el.key == "management":
            st.caption(
                "Targets are the gazetted percentages. EAP demographic adjustment, if required, "
                "is applied by your verification agency."
            )
        with st.container(border=True):

            def _ind_help(i):
                unit = "" if i.base == "bool" else "%"
                return f"Target {i.target:g}{unit} · {i.points:g} pts · cl. {i.clause}" + (
                    " · separate points line (counted inside Black people for ownership rules)"
                    if "women" in i.name.lower() or "female" in i.name.lower()
                    else ""
                )

            def _render_number(i, label):
                key = f"v_{mode}_{i.clause}"
                tag = " (DRAFT)" if i.draft_only else (" (bonus)" if i.bonus else "")
                if i.base == "bool":
                    vals[i.clause] = st.checkbox(
                        f"{label}{tag}", key=bind(key, bool(vals.get(i.clause, False)))
                    )
                    return
                rand = mode == "rand" and rand_capable(el, i)
                if rand:
                    unit = "count" if i.base == "employees" else "R"
                    lab = f"{label}{tag} ({unit})"
                elif i.base in BASE_LABEL:
                    lab = f"{label}{tag} (% of {BASE_LABEL[i.base]})"
                else:
                    lab = f"{label}{tag} (%)"
                bind(key, float(vals.get(i.clause, 0.0) or 0.0))
                # No min/max: fail-closed via validate() (Security M3 / F-EDGE-OVER100).
                vals[i.clause] = st.number_input(
                    lab,
                    step=1000.0 if rand else 0.5,
                    format="%.0f" if rand else "%.2f",
                    key=key,
                    help=_ind_help(i),
                )

            for unit in indicator_render_units(el, draft):
                if unit["kind"] == "pair":
                    st.markdown(f"**{unit['heading']}**")
                    left_lab, right_lab = unit["labels"]
                    c1, c2 = st.columns(2)
                    with c1:
                        _render_number(unit["black"], left_lab)
                    with c2:
                        _render_number(unit["women"], right_lab)
                    st.caption(
                        "Black women / Black female is scored on its own. Enter it even when "
                        "already included in the Black people figure."
                    )
                else:
                    i = unit["ind"]
                    if unit.get("women_owned"):
                        st.markdown(f"**{i.name}**")
                        _render_number(i, i.name)
                    else:
                        _render_number(i, i.name)
            used = {i.base for i in el.indicators if rand_capable(el, i)}
            if mode == "rand" and used:
                st.caption(
                    "Base from profile: "
                    + ", ".join(
                        f"{BASE_LABEL[b]} R{getattr(fin, BASE_FIN[b]) or 0:,.0f}".replace(",", " ")
                        for b in sorted(used)
                    )
                )
    for s in card.submins:
        if s.element == el.key and (draft or not s.draft_only):
            st.caption(f"Sub-minimum: {s.group or 'element'} {s.required:g} points ({s.clause}).")

    def problems():
        return [
            p.message
            for p in validate(
                card,
                store["profile"],
                fin_obj(),
                {el.key: store["values"][store["modes"].get(el.key, "pct")].get(el.key, {})}
                if ent == "ind"
                else {},
                store["modes"],
                {el.key: store["points"].get(el.key, {})} if ent == "pts" else {},
            )
        ]

    footer(problems)


# ------------------------------------------------------------------ results
def current_input(esd_override: dict | None = None):
    require_consent()
    values = {
        k: store["values"][store["modes"].get(k, "pct")].get(k, {})
        for k in {e.key for e in elements}
    }
    inp = build_input(
        S.sector,
        variant,
        store["profile"],
        fin_obj(effective=False),
        values,
        store["modes"],
        store["points"],
        S.draft,
        store["options"],
        store["entry"],
    )
    if esd_override is not None:
        row = {
            k: v for k, v in inp.indicators.get("esd", {}).items() if k not in esd_override["drop"]
        }
        row.update(esd_override["add"])
        inp.indicators["esd"] = row
    return inp


def results_step():
    require_consent()
    st.title("Your scorecard")
    st.html('<div class="bee-hex-divider" aria-hidden="true"></div>')
    badge_line()
    # F-EDGE-OVER100: validate profile even when EME deemed hides the element card.
    values = {
        k: store["values"][store["modes"].get(k, "pct")].get(k, {})
        for k in {e.key for e in elements}
    }
    ind_vals = {k: v for k, v in values.items() if store["entry"].get(k, "ind") == "ind"}
    pts_vals = {k: v for k, v in store["points"].items() if store["entry"].get(k) == "pts"}
    val_card = card
    if val_card is None and cfg.cards:
        val_card = card_for(cfg, size, variant)
    all_probs = validate(val_card, store["profile"], fin_obj(), ind_vals, store["modes"], pts_vals)
    if all_probs:
        st.error("Some inputs need fixing:\n\n" + "\n".join(f"- {p.message}" for p in all_probs))
        st.button("Go to profile", on_click=go_to, args=(0,))
        return
    calc_rate = store.setdefault("calc_rate", {"calls": 0})
    if calc_rate["calls"] >= MAX_CALCULATE_CALLS:
        st.error(
            "Too many score calculations in this session. Refresh the page to start a new session, "
            "or come back later."
        )
        st.button("Back", on_click=go_to, args=(0,))
        return
    try:
        calc_rate["calls"] += 1
        r = calculate(current_input())
    except Exception as exc:  # noqa: BLE001 - shown generically; no details or inputs logged
        st.error("We could not calculate this scorecard. Please check your inputs and try again.")
        report_unexpected(exc, what="score calculation")
        st.button("Try again", on_click=st.rerun)
        return
    c1, c2, c3 = st.columns(3)
    c1.metric(
        "Recognition level", r.level_label, f"{r.recognition_pct}% recognition", delta_color="off"
    )
    out_of = scorecard_max(card, S.draft) if card else None
    c2.metric(
        "Total points",
        "Deemed"
        if r.deemed
        else (f"{r.total_points:.1f} out of {out_of:g}" if out_of else f"{r.total_points:.1f}"),
    )
    gap = None if r.deemed or r.level_points is None else next_level_gap(r.level_points)
    c3.metric(f"To Level {gap[1]}" if gap else "Next level", f"{gap[0]:.1f} pts" if gap else "-")
    # Gender contribution metric (not a fake element). Hidden on deemed affidavit path.
    gender_x = gender_y = 0.0
    if not r.deemed and card:
        inp_for_g = current_input()
        gender_x, gender_y = gender_contribution(
            card, inp_for_g.indicators, inp_for_g.financials, S.draft
        )
        if gender_y > 0:
            st.metric(
                "Black women / Black female contribution",
                f"{gender_x:g} of {gender_y:g} pts",
            )
            st.caption(
                "Across Ownership, Management, Skills and Preferential Procurement · "
                "not a separate element"
            )
    if r.discounted and (r.total_points or 0) < 1e-9:
        # UX-M7: 0 pts is an empty state, not a "discounted from Level 9" punishment.
        st.info(
            "No points entered yet. Enter indicators or points on the earlier steps to "
            "see your recognition level and any sub-minimum effects."
        )
    elif r.discounted:
        st.warning(
            f"Sub-minimum missed: discounted from Level {r.level_before_discount} by one level."
        )
    if r.yes_applied:
        st.success("YES Initiative recognition applied.")
    elif r.yes_blocked_reason:
        st.info(f"YES not applied: {r.yes_blocked_reason}")
    with st.expander("Interpretation notes", expanded=True):
        st.caption(
            "How this calculator reads points the codes leave open. Your verification agency may read them differently."
        )
        for n in r.notes:
            st.markdown(f"- {n}")
    for w in r.warnings:
        st.warning(w)
    if r.deemed:
        st.info(
            "Deemed level from black ownership (affidavit route). Tick 'Score on the full scorecard' in the profile for a points breakdown."
        )
        st.caption(
            "PDF gap report and email unlock appear only on the full-scorecard path. "
            "A deemed affidavit result has no element gaps to report — tick that option "
            "in Profile if you want the downloadable report."
        )
        return
    names = {e.key: e.name for e in elements}
    rows = []
    for e in elements:
        mx = e.max_points(draft=S.draft)
        rows.append(
            {
                "Element": e.name,
                "Points": r.element_points.get(e.key, 0.0),
                "Max": mx,
                "Gap": max(mx - r.element_points.get(e.key, 0.0), 0.0),
            }
        )
    df = pd.DataFrame(rows)
    tf_card = any(i.group == "tf" for e in elements for i in e.indicators)
    tabs = st.tabs(
        ["Scorecard", "Sub-minimums", "Where to gain points"]
        + (["TF vs ED/SD (draft)"] if S.draft and tf_card else [])
    )
    with tabs[0]:
        if df.empty or "Element" not in df.columns:
            st.info(
                "No scorecard elements to chart yet. Enter points or indicators, "
                "or untick the full-scorecard option for a deemed EME/QSE level."
            )
        else:
            fig = go.Figure()
            fig.add_bar(
                y=df["Element"],
                x=df["Points"],
                orientation="h",
                name="Achieved",
                marker_color=GREEN,
                hovertemplate="%{y}: %{x:.1f}<extra></extra>",
            )
            fig.add_bar(
                y=df["Element"],
                x=df["Gap"],
                orientation="h",
                name="Available",
                marker=dict(
                    color=OCHRE_TINT,
                    line=dict(color=OCHRE, width=1),
                    pattern=dict(shape="/", fgcolor=OCHRE, bgcolor=OCHRE_TINT, fillmode="overlay"),
                ),
            )
            fig.update_layout(
                barmode="stack",
                height=320,
                margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(orientation="h", y=-0.18),
                font=dict(family="IBM Plex Sans, sans-serif", color=INK),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(autorange="reversed"),
                xaxis=dict(gridcolor=LINE, zerolinecolor=LINE),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        if not df.empty and "Element" in df.columns:
            st.dataframe(
                df,
                hide_index=True,
                width="stretch",
                column_config={
                    c: st.column_config.NumberColumn(format="%.1f")
                    for c in ["Points", "Max", "Gap"]
                },
            )
        else:
            st.caption("No element rows to show.")
        if r.level_points is not None and abs(r.level_points - r.total_points) > 1e-9:
            st.caption(
                f"Points used for the level table after normalisation: {r.level_points:.1f}."
            )
        with st.expander("Group detail"):
            st.dataframe(
                pd.DataFrame(
                    [
                        {"Element": names.get(k, k), "Group": g, "Points": v}
                        for k, d in r.group_points.items()
                        for g, v in d.items()
                    ]
                ),
                hide_index=True,
                width="stretch",
            )
    with tabs[1]:
        if not r.submin_checks:
            st.write("No sub-minimums apply to this scorecard.")
        for c in r.submin_checks:
            txt = f"**{names.get(c.element, c.element)}{' · ' + c.group if c.group else ''}**: {c.achieved:.1f} of {c.required:g} required ({c.clause})"
            (st.success if c.passed else st.warning)(txt)
    with tabs[2]:
        if df.empty or "Gap" not in df.columns:
            st.info("No gaps to show until element scores are entered.")
        else:
            for i, row in enumerate(df.sort_values("Gap", ascending=False).itertuples(), 1):
                if row.Gap <= 0:
                    continue
                el = next(e for e in elements if e.name == row.Element)
                tips = sorted(
                    (x for x in visible_indicators(el, S.draft) if not x.bonus),
                    key=lambda x: -x.points,
                )[:2]
                with st.container(border=True):
                    a, b = st.columns([4, 1])
                    a.markdown(
                        f"**{i}. {row.Element}**  \n"
                        + "; ".join(
                            f"{t.name}: target {t.target:g}{'' if t.base == 'bool' else '%'} ({t.points:g} pts, cl. {t.clause})"
                            for t in tips
                        )
                    )
                    b.metric("Available", f"+{row.Gap:.1f}", label_visibility="collapsed")
            g_gaps = gender_open_gaps(card, current_input().indicators, fin_obj(), S.draft)
            if g_gaps:
                st.markdown("**Black women / Black female lines**")
                st.caption(
                    "Black women indicators are scored separately from Black people indicators."
                )
                for g in g_gaps:
                    with st.container(border=True):
                        a, b = st.columns([4, 1])
                        a.markdown(
                            f"**{g['element_name']} · {g['name']}**  \n"
                            f"{g['achieved']:g} of {g['max']:g} pts · target {g['target']:g}% "
                            f"(cl. {g['clause']})"
                        )
                        b.metric(
                            "Available",
                            f"+{g['open']:.1f}",
                            label_visibility="collapsed",
                        )
    if S.draft and tf_card:
        with tabs[3]:
            tf_planner(r)
    st.divider()
    with st.container(border=True):
        st.subheader("Get your PDF gap report")
        st.caption("A printable report with your scorecard, gaps and interpretation notes.")
        gate = store.setdefault("pdf_gate", {"email": "", "marketing": False, "unlocked": False})
        rate = store.setdefault("pdf_rate", {"unlock_attempts": 0, "pdf_builds": 0})
        if not gate.get("unlocked"):
            st.markdown(
                "**If you leave an email to unlock the PDF download**  \n"
                "Your email is kept only for this interactive session on the app host so "
                "we can unlock the download. We do not email the report in v1. When the "
                "session ends, the email is discarded; it is not written to a database or "
                "other long-term store."
            )
            st.caption(
                f"Up to {MAX_PDF_UNLOCK_ATTEMPTS} unlock attempts, "
                f"{MAX_PDF_BUILDS} PDF builds, and {MAX_CALCULATE_CALLS} score calculations "
                "are allowed per browser session."
            )
            if rate["unlock_attempts"] >= MAX_PDF_UNLOCK_ATTEMPTS:
                st.error(
                    "Too many unlock attempts in this session. "
                    "Refresh the page to start a new session, or try again later."
                )
            else:
                # bind()+key only (no value=) — same B12 / MBC-BUG-01 pattern as profile.
                bind("pdf_email", gate.get("email", "") or "")
                gate["email"] = st.text_input("Work email", key="pdf_email")
                bind("pdf_mkt", bool(gate.get("marketing", False)))
                gate["marketing"] = st.checkbox(
                    "Marketing updates (optional) — does not add you to a mailing list in v1",
                    key="pdf_mkt",
                    help=(
                        "Ticking this does not add you to a mailing list in v1. We will ask "
                        "again under POPIA s69 before sending any marketing."
                    ),
                )
                st.caption(
                    "Marketing updates (optional, unticked by default): ticking this does "
                    "**not** add you to a mailing list in v1. We will ask again under "
                    "POPIA s69 before sending any marketing."
                )
                if S.get("_pdf_unlock_err"):
                    st.error(S["_pdf_unlock_err"])
                if st.button(
                    "Continue with email", type="primary", width="stretch", key="pdf_unlock"
                ):
                    rate["unlock_attempts"] += 1
                    em = (S.get("pdf_email") or gate.get("email") or "").strip()
                    gate["email"] = em
                    # Require local@domain.tld shape; reject "not-an-email" / "@@" (MBC-F02).
                    local, _, domain = em.partition("@")
                    ok = bool(local) and "." in domain and " " not in em and em.count("@") == 1
                    if ok:
                        S.pop("_pdf_unlock_err", None)
                        gate["unlocked"] = True
                        st.rerun()
                    else:
                        S["_pdf_unlock_err"] = (
                            "Please fix:\n\n- Enter a valid email address to continue."
                        )
                        st.rerun()
        else:
            st.caption(
                f"Email on file for this session: {gate['email']}. Marketing preference: "
                f"{'yes' if gate.get('marketing') else 'no'}."
            )
            company_name = store["profile"].get("company") or "Your company"
            cache_key = (
                company_name,
                label,
                S.draft,
                S.sector,
                store["profile"].get("revenue"),
                str(store.get("points")),
                str(store.get("values")),
            )
            cached = store.get("pdf_cache")
            try:
                from bee.report import render_pdf

                if cached and cached.get("key") == cache_key:
                    pdf = cached["bytes"]
                elif rate["pdf_builds"] >= MAX_PDF_BUILDS:
                    st.error(
                        f"PDF build limit reached for this session (max {MAX_PDF_BUILDS}). "
                        "Refresh the page to start a new session, or try again later."
                    )
                    pdf = None
                else:
                    with st.spinner("Building PDF…"):
                        _inp = current_input()
                        pdf = render_pdf(
                            r,
                            card,
                            store["profile"],
                            label,
                            cfg,
                            draft=S.draft,
                            company_name=company_name,
                            indicators=_inp.indicators,
                            financials=_inp.financials,
                        )
                    rate["pdf_builds"] += 1
                    store["pdf_cache"] = {"key": cache_key, "bytes": pdf}
                if pdf is not None:
                    st.download_button(
                        "Download PDF gap report",
                        pdf,
                        file_name="bee-gap-report.pdf",
                        mime="application/pdf",
                        type="primary",
                        width="stretch",
                    )
            except Exception as exc:  # noqa: BLE001 — no traceback (showErrorDetails=false)
                # Surface a clear, non-sensitive reason so Cloud/deps failures are actionable.
                detail = str(exc).strip() or type(exc).__name__
                low = detail.lower()
                if any(
                    s in low
                    for s in (
                        "pango",
                        "cairo",
                        "libgobject",
                        "cannot load library",
                        "weasyprint",
                        "gobject",
                    )
                ):
                    st.error(
                        "Could not build the PDF: the PDF engine is missing system libraries "
                        "on this host (WeasyPrint / Pango). This is a deploy configuration issue, "
                        "not your inputs — please try again after the next app update."
                    )
                else:
                    st.error(
                        f"Could not build the PDF ({type(exc).__name__}). "
                        "Please try again. If it keeps failing, contact support with the time of the attempt."
                    )
                report_unexpected(exc, what="PDF build")


def tf_planner(base):
    esd = next(e for e in elements if e.key == "esd")
    tf = next(i for i in esd.indicators if i.group == "tf")
    sd = [i for i in esd.indicators if i.group == "sd" and not i.bonus and i.base == "npat"]
    ed = [i for i in esd.indicators if i.group == "ed" and not i.bonus and i.base == "npat"]
    st.warning("DRAFT, NOT IN FORCE. Draft 2026 rules (GG 54032). Planning only.")
    npat = fin_obj().npat
    if not npat or npat <= 0:
        st.error("Enter a positive NPAT in the profile to compare the routes.")
        st.button("Go to profile", on_click=go_to, args=(0,), key="tf_prof")
        return
    if store["entry"].get("esd", "ind") != "ind":
        st.info("The planner needs ESD entered as indicators (not points).")
        return
    budget = st.slider(
        "Contribution budget (R per year)",
        0,
        int(max(npat * 0.05, 10_000)),
        int(npat * tf.target / 100),
        1_000,
    )
    st.caption(f"= {budget / npat * 100:.2f}% of NPAT. The two routes are either/or.")
    drop = {i.clause for i in sd + ed} | {tf.clause}
    weights = [(i, i.target) for i in sd + ed]
    tot_w = sum(w for _, w in weights) or 1
    routes = {
        "Transformation Fund": {"drop": drop, "add": {tf.clause: Rand(float(budget))}},
        "Direct SD + ED": {
            "drop": drop,
            "add": {i.clause: Rand(budget * w / tot_w) for i, w in weights},
        },
    }
    cols = st.columns(2)
    for col, (name, ov) in zip(cols, routes.items(), strict=True):
        try:
            res = calculate(current_input(ov))
        except Exception as exc:  # noqa: BLE001
            col.error("Could not score this route.")
            report_unexpected(exc, what="TF planner score")
            continue
        with col.container(border=True):
            st.subheader(name)
            st.metric("ESD points", f"{res.element_points.get('esd', 0):.1f}")
            st.metric(
                "New total",
                f"{res.total_points:.1f}",
                f"{res.total_points - base.total_points:+.1f}",
            )
            st.metric("Level", res.level_label)
    st.caption(
        "SD + ED budget split in proportion to their NPAT targets "
        + ", ".join(f"{i.name} {i.target:g}%" for i, _ in weights)
        + "."
    )


if S.step == 0:
    profile_step()
elif S.step == len(steps) - 1:
    results_step()
    st.button("Back", on_click=go_to, args=(S.step - 1,))
else:
    element_step(elements[S.step - 1])
