"""Pure UI logic: sector picker data, field specs, validation and ScoreInput building."""

from __future__ import annotations

from dataclasses import dataclass

from bee import CompanyProfile, Financials, Rand, ScoreInput, YesInput, YesTier
from bee.levels import LEVELS
from bee.registry import get_sector, sectors
from bee.rules import Element, Indicator, Scorecard
from bee.sectors.base import SectorConfig

PCT_ONLY_ELEMENTS = ("ownership", "management")  # Ownership & MC are percentage-only
BASE_LABEL = {
    "npat": "NPAT",
    "leviable": "leviable payroll",
    "tmps": "TMPS",
    "employees": "headcount",
}
BASE_FIN = {"npat": "npat", "leviable": "leviable_amount", "tmps": "tmps", "employees": "employees"}
# Pairs (women clause, all-black clause): women value may not exceed the all-black value.
WOMEN_PAIRS_SUFFIX = ("black women", "black females", "black female")
STATUS_BADGE = {
    "verified": None,
    "unverified": "UNVERIFIED",
    "not_loaded": "NOT LOADED",
    "legacy": "LEGACY",
    "excluded": "EXCLUDED",
    "custom": "CUSTOM",
}


def sector_choices() -> list[tuple[str, str]]:
    """(key, display name), Generic first."""
    keys = sectors()
    keys.sort(key=lambda k: (k != "generic", get_sector(k).name))
    return [(k, get_sector(k).name) for k in keys]


def size_for(cfg: SectorConfig, revenue: float, variant: str | None):
    return cfg.threshold(cfg.resolve_variant(variant)).classify(revenue)


def scorecard_label(cfg: SectorConfig, size, variant: str | None) -> str:
    raw = str(size.value if hasattr(size, "value") else size)
    size_name = cfg.size_labels.get(size, "Large" if raw == "Generic" else raw)
    v = f" ({variant})" if variant else ""
    return f"{cfg.name}{v} · {size_name} scorecard · {cfg.gazette}"


def card_for(cfg: SectorConfig, size, variant: str | None) -> Scorecard:
    return cfg.card(size, cfg.resolve_variant(variant))


def visible_indicators(el: Element, draft: bool) -> list[Indicator]:
    return [i for i in el.indicators if draft or not i.draft_only]


def rand_capable(el: Element, ind: Indicator) -> bool:
    return el.key not in PCT_ONLY_ELEMENTS and ind.base in BASE_FIN


@dataclass
class Problem:
    field: str
    message: str


def _base_value(fin: Financials, base: str) -> float | None:
    attr = BASE_FIN.get(base)
    return getattr(fin, attr) if attr else None


def validate(
    card: Scorecard, profile: dict, fin: Financials, values: dict, modes: dict, points: dict
) -> list[Problem]:
    """values: {element: {clause: number|bool}} as entered; modes: {element: 'rand'|'pct'}.
    points: {element: {group: pts}} for element-level sector cards."""
    out: list[Problem] = []
    rev = profile.get("revenue")
    if rev is None or rev < 0:
        out.append(Problem("revenue", "Total revenue must be zero or more."))
    bo = profile.get("black_ownership", 0) or 0
    if not 0 <= bo <= 100:
        out.append(Problem("black_ownership", "Black ownership must be between 0% and 100%."))
    for name, v in (
        ("leviable_amount", fin.leviable_amount),
        ("tmps", fin.tmps),
        ("employees", fin.employees),
    ):
        if v is not None and v < 0:
            out.append(Problem(name, f"{name.replace('_', ' ').title()} cannot be negative."))
    for el in card.elements:
        ev = values.get(el.key, {})
        mode = modes.get(el.key, "pct")
        by_name = {i.name.lower(): i for i in el.indicators}
        for ind in el.indicators:
            if ind.clause not in ev or ind.base == "bool":
                continue
            v = ev[ind.clause]
            if v is None:
                continue
            if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
                out.append(Problem(ind.clause, f"{ind.name}: enter a finite number."))
                continue
            if v < 0:
                out.append(Problem(ind.clause, f"{ind.name}: cannot be negative."))
                continue
            if mode == "rand" and rand_capable(el, ind):
                base = _base_value(fin, ind.base)
                if v > 0 and (not base or base <= 0):
                    out.append(
                        Problem(
                            ind.clause,
                            f"{ind.name}: enter a positive "
                            f"{BASE_LABEL[ind.base]} in the profile, or switch to "
                            "percentages (a % of a zero or negative base is undefined).",
                        )
                    )
            elif v > 100 and (
                ind.group == "net_value"
                or not (ind.base in BASE_FIN and el.key not in PCT_ONLY_ELEMENTS)
            ):
                out.append(
                    Problem(
                        ind.clause,
                        f"{ind.name}: a percentage cannot exceed 100% "
                        f"(for Net Value, that is more than {ind.points:g} points).",
                    )
                )
        # women <= all black, matched by name
        for ind in el.indicators:
            low = ind.name.lower()
            for suf in WOMEN_PAIRS_SUFFIX:
                if suf in low and not (suf == "black female" and "black females" in low):
                    parent = by_name.get(_parent_name(ind.name, suf))
                    if parent and ind.clause in ev and parent.clause in ev:
                        a, b = ev[ind.clause], ev[parent.clause]
                        if (
                            isinstance(a, (int, float))
                            and isinstance(b, (int, float))
                            and not isinstance(a, bool)
                            and a > b + 1e-9
                        ):
                            out.append(
                                Problem(
                                    ind.clause,
                                    f"{ind.name} ({a:g}) cannot exceed {parent.name} ({b:g}).",
                                )
                            )
        if points.get(el.key):
            ep = points.get(el.key, {})
            for g, v in ep.items():
                if g == "bonus":
                    if el.bonus_max is not None and v > el.bonus_max + 1e-9:
                        out.append(
                            Problem(f"{el.key}.bonus", f"{el.name} bonus: max {el.bonus_max:g}.")
                        )
                elif v > el.max_points(g) + 1e-9:
                    out.append(
                        Problem(f"{el.key}.{g}", f"{el.name} {g}: max {el.max_points(g):g} points.")
                    )
            if sum(v for g, v in ep.items() if g != "bonus") > el.max_points() + 1e-9:
                out.append(
                    Problem(
                        el.key,
                        f"{el.name}: points exceed the element weighting {el.max_points():g}.",
                    )
                )
    return out


def _parent_name(name: str, suffix: str) -> str:
    low = name.lower()
    repl = "black" if suffix == "black female" else "black people"
    return low.replace(suffix, repl)


def entry_options(el: Element) -> list[str]:
    """'ind' (raw indicator inputs) when indicator targets exist; 'pts' always."""
    return (["ind"] if el.indicators else []) + ["pts"]


def build_input(
    sector: str,
    variant: str | None,
    profile: dict,
    fin: Financials,
    values: dict,
    modes: dict,
    points: dict,
    draft: bool,
    options: dict | None = None,
    entry: dict | None = None,
) -> ScoreInput:
    """entry: {element: 'ind'|'pts'}; default 'ind' where indicators exist, else 'pts'."""
    entry = entry or {}
    cfg = get_sector(sector)
    size = size_for(cfg, profile["revenue"], variant)
    card = card_for(cfg, size, variant) if cfg.cards else None
    ind: dict[str, dict] = {}
    if card:
        for el in card.elements:
            if entry.get(el.key, entry_options(el)[0]) != "ind":
                continue
            ev = values.get(el.key, {})
            row = {}
            for i in visible_indicators(el, draft):
                if i.clause not in ev or ev[i.clause] in (None, 0, False):
                    continue
                v = ev[i.clause]
                if modes.get(el.key) == "rand" and rand_capable(el, i):
                    row[i.clause] = Rand(float(v))
                else:
                    row[i.clause] = v if isinstance(v, bool) else float(v)
            if row:
                ind[el.key] = row
    pts = {
        k: {g: float(v) for g, v in d.items() if v}
        for k, d in points.items()
        if card is None
        or not card.has(k)
        or entry.get(k, entry_options(card.element(k))[0]) == "pts"
    }
    pts = {k: d for k, d in pts.items() if d}
    return ScoreInput(
        profile=CompanyProfile(
            total_revenue=profile["revenue"],
            black_ownership_pct=profile.get("black_ownership", 0.0),
            sector=sector,
            variant=variant,
            opt_scored=profile.get("opt_scored", False),
        ),
        financials=fin,
        indicators=ind,
        points=pts,
        yes=YesInput(YesTier(profile.get("yes_tier", "none")), profile.get("yes_prev_level")),
        draft_rules=draft,
        options=dict(options or {}),
    )


def next_level_gap(points: float) -> tuple[float, int] | None:
    """Points needed to reach the next level (by the level table), or None at Level 1."""
    for minimum, level, _ in reversed(LEVELS):
        if points < minimum - 1e-9:
            return round(minimum - points, 2), level
    return None


def to_rand(pct: float, base: float | None) -> float:
    return 0.0 if not base or base <= 0 else pct * base / 100


def to_pct(amount: float, base: float | None) -> float:
    return 0.0 if not base or base <= 0 else amount / base * 100
