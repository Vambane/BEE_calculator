"""BEE Check: thin Streamlit UI over the ``bee`` engine (design spec v1.1).

All scoring is done by ``bee.calculate``; this file only collects inputs, validates them and
renders results. No inputs are logged. Run: ``streamlit run app.py``.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from bee import Financials, Rand, calculate
from bee.registry import get_sector
from bee_ui.core import (
    BASE_FIN,
    BASE_LABEL,
    PCT_ONLY_ELEMENTS,
    build_input,
    card_for,
    entry_options,
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

GREEN, OCHRE, OCHRE_TINT, LINE, INK = "#1F5C4F", "#C8892B", "#F7ECD9", "#DDD8CC", "#14302B"
MODES = {"rand": "Rand amounts", "pct": "Percentages"}
ENTRY = {"ind": "Indicators", "pts": "Points (pre-calculated)"}
DRAFT_LABEL = "Draft 2026 rules (Transformation Fund)"

st.set_page_config(page_title="BEE Check", layout="centered")
st.markdown("<style>.block-container{max-width:960px}</style>", unsafe_allow_html=True)

Q = st.query_params
S = st.session_state
S.setdefault("sector", Q.get("sector", "generic"))
S.setdefault("draft", Q.get("draft", "0") == "1")
S.setdefault("default_mode", "pct" if Q.get("mode") == "pct" else "rand")
# Canonical store: widget state is dropped for unrendered steps, so values live here.
S.setdefault(
    "store",
    {
        "profile": {
            "company": "",
            "revenue": 0.0,
            "black_ownership": 0.0,
            "variant": None,
            "yes_tier": "none",
            "yes_prev_level": None,
            "opt_scored": False,
        },
        "fin": {"npat": 0.0, "leviable_amount": 0.0, "tmps": 0.0, "employees": 0.0},
        "values": {"rand": {}, "pct": {}},
        "modes": {},
        "entry": {},
        "points": {},
        "options": {},
        "consent": False,
    },
)
store = S.store
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
    st.info("EXAMPLE DATA: illustrative inputs (points entry), not a real company.")
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


def fin_obj() -> Financials:
    f = store["fin"]
    return Financials(
        npat=f["npat"] or None,
        leviable_amount=f["leviable_amount"] or None,
        tmps=f["tmps"] or None,
        employees=f["employees"] or None,
    )


def context():
    cfg = get_sector(S.sector)
    variant = store["profile"]["variant"] if cfg.variants else None
    if variant not in (cfg.variants or (None,)):
        variant = cfg.default_variant
    size = size_for(cfg, store["profile"]["revenue"], variant)
    card = card_for(cfg, size, variant) if size.value != "EME" else None
    return cfg, variant, size, card


cfg, variant, size, card = context()
if S.get("demo_seeded") and card and not store["points"]:
    for e in card.elements:  # demo: 60% of every group's maximum, entered as points
        store["entry"][e.key] = "pts"
        gs = [g for g in e.groups() if g != "tf"]
        if e.total is not None and sum(dict(e.group_max).values()) >= e.total:
            gs = [g for g in gs if g != "main"]
        store["points"][e.key] = {
            g: round(0.6 * e.max_points(g), 1) for g in gs if e.max_points(g) > 0
        }
elements = [e for e in card.elements if e.max_points() > 0] if card else []  # hide 0-max elements
steps = ["Profile", *[e.name for e in elements], "Results"]
S.step = min(S.step, len(steps) - 1)
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
    if not store.get("consent"):
        S.step = 0
        return
    S.step = n


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
    for i, s in enumerate(steps):
        st.markdown(f"**→ {s}**" if i == S.step else ("✓ " if i < S.step else "○ ") + s)
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
    with st.container(border=True):
        st.markdown(
            "**Privacy notice.** We use the figures you enter only to calculate your "
            "scorecard in this session. Aggregate black ownership and management-control "
            "figures are race- and gender-related special personal information "
            "(POPIA s26), used only for this session's calculation and not retained after "
            "you close the page. Nothing you enter is logged. Do not enter ID numbers or "
            "individuals' names."
        )
        store["consent"] = st.checkbox(
            "I understand and consent to my company figures being processed for this calculation.",
            value=store["consent"],
        )
    consented = bool(store["consent"])
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
        p["revenue"] = st.number_input(
            "Total revenue, last financial year (R)",
            min_value=0.0,
            value=float(p["revenue"]),
            step=500_000.0,
            format="%.0f",
            disabled=not consented,
        )
        p["black_ownership"] = st.number_input(
            "Black ownership (%)",
            min_value=0.0,
            max_value=100.0,
            value=float(p["black_ownership"]),
            step=1.0,
            disabled=not consented,
        )
        cfg2, _, size2, _ = context()
        st.caption(f":green-badge[Size: {cfg2.size_labels.get(size2, size2.value)}]")
        st.markdown(
            f"**Scorecard: {scorecard_label(cfg2, size2, p['variant'] if cfg2.variants else None)}**"
        )
        f = store["fin"]
        a, b = st.columns(2)
        f["leviable_amount"] = a.number_input(
            "Leviable payroll (R)",
            0.0,
            value=float(f["leviable_amount"]),
            step=100_000.0,
            format="%.0f",
            disabled=not consented,
        )
        f["npat"] = b.number_input(
            "Net profit after tax (R)",
            value=float(f["npat"]),
            step=100_000.0,
            format="%.0f",
            disabled=not consented,
        )
        a, b = st.columns(2)
        f["tmps"] = a.number_input(
            "Total measured procurement spend (R)",
            0.0,
            value=float(f["tmps"]),
            step=100_000.0,
            format="%.0f",
            disabled=not consented,
        )
        f["employees"] = b.number_input(
            "Headcount (employees)",
            0.0,
            value=float(f["employees"]),
            step=1.0,
            format="%.0f",
            disabled=not consented,
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
        cfg_, _, _, card_ = context()
        if card_:
            out += [p.message for p in validate(card_, store["profile"], fin_obj(), {}, {}, {})]
        return out

    footer(problems)


# ------------------------------------------------------------------ element steps
def element_step(el):
    require_consent()
    st.title(el.name)
    draft = S.draft
    opts = entry_options(el)
    ent = store["entry"].get(el.key, opts[0])
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
        with st.container(border=True):
            for i in visible_indicators(el, draft):
                if i is nv:
                    continue
                key = f"v_{mode}_{i.clause}"
                tag = " (DRAFT)" if i.draft_only else (" (bonus)" if i.bonus else "")
                if i.base == "bool":
                    vals[i.clause] = st.checkbox(
                        f"{i.name}{tag}", key=bind(key, bool(vals.get(i.clause, False)))
                    )
                    continue
                rand = mode == "rand" and rand_capable(el, i)
                if rand:
                    unit = "count" if i.base == "employees" else "R"
                    lab = f"{i.name}{tag} ({unit})"
                elif i.base in BASE_LABEL:
                    lab = f"{i.name}{tag} (% of {BASE_LABEL[i.base]})"
                else:
                    lab = f"{i.name}{tag} (%)"
                bind(key, float(vals.get(i.clause, 0.0) or 0.0))
                vals[i.clause] = st.number_input(
                    lab,
                    min_value=0.0,
                    max_value=None if rand else 100.0,
                    step=1000.0 if rand else 0.5,
                    format="%.0f" if rand else "%.2f",
                    key=key,
                    help=f"Target {i.target:g}{'%' if i.base != 'bool' else ''} · "
                    f"{i.points:g} pts · cl. {i.clause}",
                )
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
        fin_obj(),
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
    badge_line()
    all_probs = []
    if card:
        values = {
            k: store["values"][store["modes"].get(k, "pct")].get(k, {})
            for k in {e.key for e in elements}
        }
        ind_vals = {k: v for k, v in values.items() if store["entry"].get(k, "ind") == "ind"}
        pts_vals = {k: v for k, v in store["points"].items() if store["entry"].get(k) == "pts"}
        all_probs = validate(card, store["profile"], fin_obj(), ind_vals, store["modes"], pts_vals)
    if all_probs:
        st.error("Some inputs need fixing:\n\n" + "\n".join(f"- {p.message}" for p in all_probs))
        st.button("Go to profile", on_click=go_to, args=(0,))
        return
    try:
        r = calculate(current_input())
    except Exception:  # noqa: BLE001 - shown generically; no details or inputs logged
        st.error("We could not calculate this scorecard. Please check your inputs and try again.")
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
    if r.discounted:
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
        fig = go.Figure()
        fig.add_bar(
            y=df.Element,
            x=df.Points,
            orientation="h",
            name="Achieved",
            marker_color=GREEN,
            hovertemplate="%{y}: %{x:.1f}<extra></extra>",
        )
        fig.add_bar(
            y=df.Element,
            x=df.Gap,
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
            xaxis=dict(gridcolor=LINE),
        )
        st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        st.dataframe(
            df,
            hide_index=True,
            width="stretch",
            column_config={
                c: st.column_config.NumberColumn(format="%.1f") for c in ["Points", "Max", "Gap"]
            },
        )
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
        for i, row in enumerate(df.sort_values("Gap", ascending=False).itertuples(), 1):
            if row.Gap <= 0:
                continue
            el = next(e for e in elements if e.name == row.Element)
            tips = sorted(
                (x for x in visible_indicators(el, S.draft) if not x.bonus), key=lambda x: -x.points
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
    if S.draft and tf_card:
        with tabs[3]:
            tf_planner(r)
    st.divider()
    with st.container(border=True):
        st.subheader("Get your PDF gap report")
        st.caption("A printable report with your scorecard, gaps and interpretation notes.")
        gate = store.setdefault("pdf_gate", {"email": "", "marketing": False, "unlocked": False})
        if not gate.get("unlocked"):
            st.markdown(
                "Enter your email to unlock the download. We use it only to send the report "
                "if you ask us to (POPIA)."
            )
            gate["email"] = st.text_input("Work email", gate.get("email", ""), key="pdf_email")
            gate["marketing"] = st.checkbox(
                "Send me occasional B-BBEE updates (optional)",
                value=gate.get("marketing", False),
                key="pdf_mkt",
            )
            if st.button("Continue with email", type="primary", width="stretch", key="pdf_unlock"):
                em = (gate.get("email") or "").strip()
                if "@" in em and "." in em.split("@")[-1]:
                    gate["unlocked"] = True
                    st.rerun()
                else:
                    st.error("Please fix:\n\n- Enter a valid email address to continue.")
        else:
            st.caption(
                f"Signed in as {gate['email']}. Marketing opt-in: "
                f"{'yes' if gate.get('marketing') else 'no'}."
            )
            try:
                from bee.report import render_pdf

                with st.spinner("Building PDF…"):
                    pdf = render_pdf(
                        r,
                        card,
                        store["profile"],
                        label,
                        cfg,
                        draft=S.draft,
                        company_name=store["profile"].get("company") or "Your company",
                    )
                st.download_button(
                    "Download PDF gap report",
                    pdf,
                    file_name="bee-gap-report.pdf",
                    mime="application/pdf",
                    type="primary",
                    width="stretch",
                )
            except Exception:  # noqa: BLE001 — no details (showErrorDetails=false)
                st.error("Could not build the PDF. Please try again.")


def tf_planner(base):
    esd = next(e for e in elements if e.key == "esd")
    tf = next(i for i in esd.indicators if i.group == "tf")
    sd = [i for i in esd.indicators if i.group == "sd" and not i.bonus and i.base == "npat"]
    ed = [i for i in esd.indicators if i.group == "ed" and not i.bonus and i.base == "npat"]
    st.warning("DRAFT, NOT IN FORCE. Draft 2026 rules (GG 54032). Planning only.")
    npat = store["fin"]["npat"]
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
        except Exception:  # noqa: BLE001
            col.error("Could not score this route.")
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
