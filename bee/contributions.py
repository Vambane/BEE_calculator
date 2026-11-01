"""Value ED, SD and SED contributions with the gazetted benefit factors.

A contribution only counts at its *recognised* value: a R100 000 interest-free loan is worth
R70 000 on the scorecard, a R100 000 guarantee R50 000. Sources:

- ESD (Supplier and Enterprise Development): Statement 400 Annexe 400(B), GG 42496 (2019).
  The 2019 amendment set guarantees at 50%; the 2013 Codes (which the sector codes and the
  QSE code follow) used 3%, so non-Generic cards use 3% (flagged).
- SED: Statement 500 Annexe 500(A), Amended Codes 2013. SED takes grants, costs, discounts
  and people's time only; loans, guarantees and equity are not SED contributions.
- Rate types: a lower interest rate is recognised at (prime - actual rate) of the outstanding
  loan; a lower dividend at (ordinary dividend rate - actual rate) of the investment.
- Shorter payment periods (SD) use a special formula and are entered by hand.

Each line is assigned to one NPAT-based contribution indicator of the scorecard, so the same
model serves the Generic, QSE and sector cards. Pure Python.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from bee.rules import Indicator, Scorecard

# key: (label, ESD factor %, SED factor % or None if not an SED contribution, rate type)
# A rate type's factor is the difference between the two rates entered on the line.
TYPES: dict[str, tuple[str, float | None, float | None, bool]] = {
    "grant": ("Grant", 100, 100, False),
    "direct_cost": ("Direct costs of support", 100, 100, False),
    "discount": ("Discount beyond normal business discount", 100, 100, False),
    "overhead": ("Overhead costs (incl. dedicated staff)", 70, 80, False),
    "interest_free_loan": ("Interest-free loan, no security", 70, None, False),
    "standard_loan": ("Standard loan", 50, None, False),
    "guarantee": ("Guarantee for a beneficiary", 50, None, False),
    "lower_interest": ("Loan at a lower interest rate", None, None, True),
    "minority_equity": ("Minority equity investment", 70, None, False),
    "lower_dividend": ("Investment at a lower dividend", None, None, True),
    "prof_free": ("Professional services at no cost", 60, 80, False),
    "prof_discount": ("Professional services at a discount", 60, 80, False),
    "employee_time": ("Employee time (monthly salary / 160 x hours)", 60, 80, False),
}
GUARANTEE_2013 = 3.0  # Annexe 400(B) before the 2019 amendment
ESD_ONLY = {k for k, (_, _, sed, rate) in TYPES.items() if sed is None or rate}
RATE_LABELS = {
    "lower_interest": ("Prime rate %", "Actual rate %"),
    "lower_dividend": ("Ordinary dividend rate %", "Actual dividend rate %"),
}
LABEL_TO_TYPE = {label.lower(): k for k, (label, *_) in TYPES.items()}

COLUMNS: tuple[tuple[str, str], ...] = (
    ("beneficiary", "Beneficiary"),
    ("indicator", "Counts towards"),
    ("type", "Contribution type"),
    ("amount", "Amount (R)"),
    ("rate_a", "Prime / ordinary rate %"),
    ("rate_b", "Actual rate %"),
)
HEADER_TO_FIELD = {label.lower(): key for key, label in COLUMNS} | {k: k for k, _ in COLUMNS}


@dataclass(frozen=True)
class Target:
    """An NPAT-based contribution indicator a line can count towards."""

    element: str
    indicator: Indicator

    @property
    def is_sed(self) -> bool:
        return self.element == "sed"

    @property
    def label(self) -> str:
        return self.indicator.name


def targets(card: Scorecard, element: str | None = None) -> list[Target]:
    """NPAT-based, non-bonus, non-draft contribution indicators on the ESD and SED elements."""
    out = []
    for el in card.elements:
        if el.key not in ("esd", "sed") or (element and el.key != element):
            continue
        for ind in el.indicators:
            if ind.base == "npat" and not ind.bonus and not ind.draft_only:
                out.append(Target(el.key, ind))
    return out


def factor(type_key: str, target: Target, card_key: str, rates=(None, None)) -> float:
    """Benefit factor % for a contribution type on a target. Raises ValueError if the type
    does not apply (e.g. a loan to SED) or rates are missing."""
    label, esd, sed, is_rate = TYPES[type_key]
    if target.is_sed and type_key in ESD_ONLY:
        raise ValueError(f"{label} is not an SED contribution (Annexe 500(A))")
    if is_rate:
        a, b = rates
        if a is None or b is None:
            raise ValueError(f"{label}: enter both rates")
        if a < b:
            raise ValueError(f"{label}: actual rate is above the reference rate, so no benefit")
        return a - b
    if type_key == "guarantee" and card_key != "generic":
        return GUARANTEE_2013
    return float(sed if target.is_sed else esd)  # type: ignore[arg-type]


@dataclass(frozen=True)
class Contribution:
    beneficiary: str
    clause: str  # target indicator clause
    type: str
    amount: float
    factor_pct: float

    @property
    def recognised(self) -> float:
        return self.amount * self.factor_pct / 100


@dataclass(frozen=True)
class RowError:
    row: int
    column: str
    message: str

    def __str__(self) -> str:
        return f"Row {self.row}, {self.column}: {self.message}"


@dataclass
class ContributionSummary:
    by_clause: dict[str, float]  # recognised rand per target indicator
    gross_by_clause: dict[str, float]  # face value per target indicator
    lines: int
    notes: list[str] = field(default_factory=list)

    def percent_of(self, clause: str, base: float | None) -> float | None:
        if not base or base <= 0:
            return None
        return self.by_clause.get(clause, 0.0) / base * 100


def _text(v: object) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return str(v).strip()


def _num(v: object) -> float | None:
    if isinstance(v, bool):
        return None
    if isinstance(v, int | float):
        return float(v) if math.isfinite(v) else None
    s = _text(v).lower().removeprefix("r").replace(" ", "").replace(",", "").replace("%", "")
    if not s:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def parse_rows(
    rows: Iterable[Mapping[str, object]], card: Scorecard, element: str | None = None
) -> tuple[list[Contribution], list[RowError]]:
    """Validate lines. ``Counts towards`` may be the indicator name or clause."""
    tg = targets(card, element)
    by_key = {t.indicator.clause.lower(): t for t in tg} | {t.label.lower(): t for t in tg}
    only = tg[0] if len(tg) == 1 else None
    out: list[Contribution] = []
    errors: list[RowError] = []
    for n, raw in enumerate(rows, start=1):
        row = {HEADER_TO_FIELD.get(str(k).strip().lower(), str(k)): v for k, v in raw.items()}
        if all(_text(v) == "" for v in row.values()):
            continue
        errs: list[RowError] = []
        target = by_key.get(_text(row.get("indicator")).lower()) or (
            only if not _text(row.get("indicator")) else None
        )
        if target is None:
            names = "; ".join(t.label for t in tg) or "none on this scorecard"
            errs.append(RowError(n, "Counts towards", f"choose one of: {names}"))
        tkey = _text(row.get("type")).lower()
        tkey = tkey if tkey in TYPES else LABEL_TO_TYPE.get(tkey, "")
        if not tkey:
            errs.append(RowError(n, "Contribution type", "choose a type from the list"))
        amount = _num(row.get("amount"))
        if amount is None:
            errs.append(RowError(n, "Amount (R)", "enter a rand amount"))
        elif amount < 0:
            errs.append(RowError(n, "Amount (R)", "cannot be negative"))
        rates = (_num(row.get("rate_a")), _num(row.get("rate_b")))
        for col, r in zip(("Prime / ordinary rate %", "Actual rate %"), rates, strict=True):
            if r is not None and not 0 <= r <= 100:
                errs.append(RowError(n, col, "must be between 0 and 100"))
        f = None
        if target is not None and tkey and not errs:
            try:
                f = factor(tkey, target, card.key, rates)
            except ValueError as exc:
                errs.append(RowError(n, "Contribution type", str(exc)))
        if errs:
            errors.extend(errs)
            continue
        out.append(
            Contribution(
                _text(row.get("beneficiary")) or f"Line {n}",
                target.indicator.clause,  # type: ignore[union-attr]
                tkey,
                float(amount),  # type: ignore[arg-type]
                float(f),  # type: ignore[arg-type]
            )
        )
    return out, errors


def summarise(lines: Iterable[Contribution], card: Scorecard) -> ContributionSummary:
    lines = list(lines)
    rec: dict[str, float] = {}
    gross: dict[str, float] = {}
    for c in lines:
        rec[c.clause] = rec.get(c.clause, 0.0) + c.recognised
        gross[c.clause] = gross.get(c.clause, 0.0) + c.amount
    notes = []
    if card.key != "generic" and any(c.type == "guarantee" for c in lines):
        notes.append(
            "Guarantees valued at 3% (2013 Codes, which this scorecard follows); the 2019 "
            "Generic amendment uses 50%. Confirm with your verification agency."
        )
    if card.key not in ("generic", "qse"):
        notes.append(
            "Benefit factors are the generic Annexe 400(B) / 500(A) values; this sector code may "
            "set its own (UNVERIFIED)."
        )
    return ContributionSummary(rec, gross, len(lines), notes)
