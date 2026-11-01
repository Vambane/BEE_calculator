"""Preferential Procurement from a supplier list (Statement 400 / Code Series 600 / sectors).

An accountant's procurement working paper, as code: each supplier line carries its spend,
B-BBEE level, size and ownership. From the list this module derives

- **TMPS** (Total Measured Procurement Spend): all spend less the lines tagged as excluded;
- **recognised spend** per procurement measure: spend from *Empowering Suppliers* only,
  multiplied by the supplier's procurement recognition % (Level 1 = 135% ... Level 8 = 10%,
  non-compliant or no certificate = 0%);
- the **% of TMPS** each scorecard indicator needs, matched to the indicator by what it
  measures, so one list feeds the Generic, QSE and every loaded sector scorecard.

Interpretations (flagged in the UI and docs; confirm with the verification agency):
- Every measure is recognition-weighted and counts Empowering Suppliers only, including the
  QSE/EME, black-owned, black-women-owned and designated-group measures.
- "Designated group" means at least 51% owned by black people from designated groups; the
  supplier must also be at least 51% black owned to count.
- The exclusion categories are the common TMPS exclusions; the user tags each line and
  remains responsible for applying the exclusions correctly.
- Enhanced recognition multipliers (if any apply to a sector) are not modelled.

Pure Python: no pandas or Streamlit, so the engine and tests stay light.
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from bee.levels import NON_COMPLIANT, RECOGNITION
from bee.rules import Element, Indicator

# ------------------------------------------------------------------------------ constants

EXCLUSIONS: dict[str, str] = {
    "": "Included in TMPS",
    "tax": "Taxes, levies and duties",
    "payroll": "Salaries, wages, pension and medical aid",
    "import": "Imports with no local supplier",
    "state_monopoly": "Organ of state / public entity monopoly",
    "contribution": "ED, SD or SED contribution (scored elsewhere)",
    "other": "Other exclusion agreed with the verifier",
}

SIZES: tuple[str, ...] = ("EME", "QSE", "Large", "Unknown")

METRICS: dict[str, str] = {
    "all": "All Empowering Suppliers",
    "qse": "QSE Empowering Suppliers",
    "eme": "EME Empowering Suppliers",
    "bo51": "At least 51% black-owned",
    "bwo30": "At least 30% black-women-owned",
    "bwo35": "At least 35% black-women-owned",
    "bwo51": "At least 51% black-women-owned",
    "designated": "At least 51% black-owned, designated group",
}

# CSV / table columns, in template order. ``label`` is the header users see.
COLUMNS: tuple[tuple[str, str], ...] = (
    ("supplier", "Supplier"),
    ("spend", "Spend (R)"),
    ("level", "B-BBEE level"),
    ("size", "Size"),
    ("black_ownership_pct", "Black ownership %"),
    ("black_women_ownership_pct", "Black women ownership %"),
    ("designated_group", "Designated group"),
    ("empowering", "Empowering supplier"),
    ("exclusion", "TMPS exclusion"),
)
HEADER_TO_FIELD = {label.lower(): key for key, label in COLUMNS} | {k: k for k, _ in COLUMNS}

TEMPLATE_ROWS: tuple[tuple[str, ...], ...] = (
    ("Example Logistics (Pty) Ltd", "1250000", "1", "QSE", "100", "60", "no", "yes", ""),
    ("Example Office Supplies CC", "320000", "4", "EME", "30", "0", "no", "yes", ""),
    ("SARS", "900000", "", "Unknown", "0", "0", "no", "no", "tax"),
)

MAX_ROWS = 5000  # guard against runaway uploads

_TRUE = {"yes", "y", "true", "1", "x", "✓"}
_FALSE = {"no", "n", "false", "0", ""}


# ------------------------------------------------------------------------------ models


@dataclass(frozen=True)
class Supplier:
    name: str
    spend: float
    level: int = NON_COMPLIANT  # 1..8; 9 = non-compliant or no certificate
    size: str = "Unknown"
    black_ownership_pct: float = 0.0
    black_women_ownership_pct: float = 0.0
    designated_group: bool = False
    empowering: bool = True
    exclusion: str = ""

    @property
    def excluded(self) -> bool:
        return bool(self.exclusion)

    @property
    def recognition_pct(self) -> int:
        return RECOGNITION[self.level]

    @property
    def recognised_spend(self) -> float:
        """Spend counted towards the procurement measures (0 if excluded or not empowering)."""
        if self.excluded or not self.empowering:
            return 0.0
        return self.spend * self.recognition_pct / 100

    def metrics(self) -> tuple[str, ...]:
        """Procurement measures this supplier's recognised spend counts towards."""
        if self.excluded or not self.empowering:
            return ()
        out = ["all"]
        if self.size == "QSE":
            out.append("qse")
        if self.size == "EME":
            out.append("eme")
        bo, bwo = self.black_ownership_pct, self.black_women_ownership_pct
        if bo >= 51:
            out.append("bo51")
            if self.designated_group:
                out.append("designated")
        for threshold, key in ((30, "bwo30"), (35, "bwo35"), (51, "bwo51")):
            if bwo >= threshold:
                out.append(key)
        return tuple(out)


@dataclass(frozen=True)
class RowError:
    row: int  # 1-based data row, as a user counts rows in a spreadsheet
    column: str
    message: str

    def __str__(self) -> str:
        return f"Row {self.row}, {self.column}: {self.message}"


@dataclass
class ProcurementSummary:
    suppliers: int
    total_spend: float
    excluded: dict[str, float]  # exclusion key -> rand
    tmps: float
    recognised: dict[str, float]  # metric key -> recognised rand
    no_certificate_spend: float  # included spend from suppliers with no level / NC
    non_empowering_spend: float  # included spend from suppliers that are not empowering
    notes: list[str] = field(default_factory=list)

    @property
    def excluded_total(self) -> float:
        return sum(self.excluded.values())

    def percent(self, metric: str) -> float:
        """Recognised spend for ``metric`` as a % of TMPS (0 when TMPS is 0)."""
        if self.tmps <= 0:
            return 0.0
        return self.recognised.get(metric, 0.0) / self.tmps * 100

    def indicator_values(self, element: Element) -> tuple[dict[str, float], list[Indicator]]:
        """``({clause: % of TMPS}, unmatched)`` for an element's procurement indicators.

        Unmatched are TMPS-based indicators this module cannot measure from the list; the
        user enters those by hand.
        """
        values: dict[str, float] = {}
        unmatched: list[Indicator] = []
        for ind in element.indicators:
            if ind.base != "tmps":
                continue
            metric = classify_indicator(ind)
            if metric is None:
                unmatched.append(ind)
            else:
                values[ind.clause] = self.percent(metric)  # full precision
        return values, unmatched


# ------------------------------------------------------------------------------ matching

_QSE = re.compile(r"\bqses?\b")
_EME = re.compile(r"\bemes?\b")
_PCT = re.compile(r"(\d+(?:\.\d+)?)\s*%")


def classify_indicator(ind: Indicator) -> str | None:
    """Map a procurement indicator to the measure it needs, from its gazetted name."""
    if ind.base != "tmps":
        return None
    n = ind.name.lower()
    pct = _PCT.search(n)
    threshold = float(pct.group(1)) if pct else None
    if "designated" in n:
        return "designated"
    if "women" in n or "female" in n:
        return {30.0: "bwo30", 35.0: "bwo35", 51.0: "bwo51"}.get(threshold or 30.0)
    if "black owned" in n or "black-owned" in n:
        return "bo51" if threshold in (None, 51.0) else None
    if _QSE.search(n):
        return "qse"
    if _EME.search(n):
        return "eme"
    if "all empowering" in n:
        return "all"
    return None


def procurement_indicators(element: Element) -> list[Indicator]:
    """TMPS-based indicators of an element (empty if the element has no procurement table)."""
    return [i for i in element.indicators if i.base == "tmps"]


# ------------------------------------------------------------------------------ parsing


def _text(v: object) -> str:
    if v is None:
        return ""
    if isinstance(v, float) and math.isnan(v):
        return ""
    return str(v).strip()


def _number(raw: object) -> float | None:
    """Parse '1 250 000', 'R1,250,000.50', '51%', 51 -> float. None if blank or invalid."""
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int | float):
        return float(raw) if math.isfinite(raw) else None
    s = _text(raw).lower().removeprefix("r")
    s = s.replace("%", "").replace(" ", "").replace(" ", "").replace(",", "")
    if not s:
        return None
    try:
        x = float(s)
    except ValueError:
        return None
    return x if math.isfinite(x) else None


def _bool(raw: object) -> bool | None:
    if isinstance(raw, bool):
        return raw
    s = _text(raw).lower()
    if s in _TRUE:
        return True
    if s in _FALSE:
        return False
    return None


def _level(raw: object) -> int | None:
    """'1', 1, 'L2', 'Level 3' -> int; '', 'NC', 'non-compliant', 'none', '9' -> 9."""
    if isinstance(raw, int | float) and not isinstance(raw, bool):
        if isinstance(raw, float) and not math.isfinite(raw):
            return NON_COMPLIANT
        if float(raw).is_integer() and 1 <= int(raw) <= 9:
            return int(raw)
        return None
    s = _text(raw).lower().replace("level", "").replace(" ", "")
    if s in ("", "nc", "non-compliant", "noncompliant", "none", "n/a", "na", "-"):
        return NON_COMPLIANT
    s = s.removeprefix("l")
    if s.isdigit() and 1 <= int(s) <= 9:
        return int(s)
    try:
        f = float(s)
    except ValueError:
        return None
    return int(f) if f.is_integer() and 1 <= f <= 9 else None


def _size(raw: object) -> str | None:
    s = _text(raw).lower()
    if s in ("", "unknown", "?"):
        return "Unknown"
    if s in ("eme", "emes"):
        return "EME"
    if s in ("qse", "qses"):
        return "QSE"
    if s in ("large", "generic", "le", "large enterprise"):
        return "Large"
    return None


def _exclusion(raw: object) -> str | None:
    s = _text(raw).lower()
    if s in ("", "no", "none", "included", "n", EXCLUSIONS[""].lower()):
        return ""
    for key, label in EXCLUSIONS.items():
        if key and (s == key or s == label.lower()):
            return key
    return None


def _pct_or_zero(raw: object) -> float | None:
    """Blank ownership means 0%; anything else must parse."""
    return _number(raw) if _text(raw) else 0.0


def _is_blank(row: Mapping[str, object]) -> bool:
    return all(_text(v) == "" for v in row.values())


def parse_rows(rows: Iterable[Mapping[str, object]]) -> tuple[list[Supplier], list[RowError]]:
    """Validate raw rows (CSV dicts or table records) into suppliers.

    Headers may be the field keys or the column labels (case-insensitive). Blank rows are
    skipped. Every problem is returned, not just the first, so a user can fix the sheet in
    one pass.
    """
    suppliers: list[Supplier] = []
    errors: list[RowError] = []
    for n, raw in enumerate(rows, start=1):
        if n > MAX_ROWS:
            errors.append(RowError(n, "Supplier", f"more than {MAX_ROWS} rows; split the list"))
            break
        row = {HEADER_TO_FIELD.get(str(k).strip().lower(), str(k)): v for k, v in raw.items()}
        if _is_blank(row):
            continue
        errs: list[RowError] = []

        def bad(col: str, msg: str, _errs: list[RowError] = errs, _n: int = n) -> None:
            _errs.append(RowError(_n, col, msg))

        name = _text(row.get("supplier")) or f"Supplier {n}"
        spend = _number(row.get("spend"))
        if spend is None:
            bad("Spend (R)", "enter a rand amount")
        elif spend < 0:
            bad("Spend (R)", "cannot be negative; net credit notes into the supplier's spend")
        level = _level(row.get("level"))
        if level is None:
            bad("B-BBEE level", "use 1 to 8, or leave blank / NC for no certificate")
        size = _size(row.get("size"))
        if size is None:
            bad("Size", "use EME, QSE, Large or Unknown")
        bo = _pct_or_zero(row.get("black_ownership_pct"))
        bwo = _pct_or_zero(row.get("black_women_ownership_pct"))
        for col, v in (("Black ownership %", bo), ("Black women ownership %", bwo)):
            if v is None or not 0 <= v <= 100:
                bad(col, "must be between 0 and 100")
        if bo is not None and bwo is not None and 0 <= bo <= 100 and bwo > bo:
            bad("Black women ownership %", "cannot exceed black ownership %")
        designated = _bool(row.get("designated_group"))
        if designated is None:
            bad("Designated group", "use yes or no")
        emp_raw = row.get("empowering")
        blank_emp = _text(emp_raw) == "" and not isinstance(emp_raw, bool)
        empowering = True if blank_emp else _bool(emp_raw)  # blank = yes (certificate default)
        if empowering is None:
            bad("Empowering supplier", "use yes or no")
        exclusion = _exclusion(row.get("exclusion"))
        if exclusion is None:
            keys = ", ".join(k for k in EXCLUSIONS if k)
            bad("TMPS exclusion", f"leave blank to include, or use one of: {keys}")
        if errs:
            errors.extend(errs)
            continue
        suppliers.append(
            Supplier(
                name=name,
                spend=float(spend),  # type: ignore[arg-type]
                level=int(level),  # type: ignore[arg-type]
                size=str(size),
                black_ownership_pct=float(bo),  # type: ignore[arg-type]
                black_women_ownership_pct=float(bwo),  # type: ignore[arg-type]
                designated_group=bool(designated),
                empowering=bool(empowering),
                exclusion=str(exclusion),
            )
        )
    return suppliers, errors


def parse_csv(text: str) -> tuple[list[Supplier], list[RowError]]:
    """Parse a supplier-list CSV (the template's columns; extra columns are ignored)."""
    text = text.lstrip("﻿")  # Excel's UTF-8 BOM
    sample = text[:2048]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    fields = {HEADER_TO_FIELD.get((h or "").strip().lower()) for h in (reader.fieldnames or [])}
    missing = [label for key, label in COLUMNS[:3] if key not in fields]
    if missing:
        return [], [RowError(0, "Header", f"missing column(s): {', '.join(missing)}")]
    return parse_rows(reader)


def level_label(level: int) -> str:
    return "NC" if level == NON_COMPLIANT else str(level)


LEVEL_OPTIONS: tuple[str, ...] = (*(str(i) for i in range(1, 9)), "NC")


def to_record(s: Supplier) -> dict[str, object]:
    """One supplier as a label-keyed row (the editable table and the CSV export)."""
    return {
        "Supplier": s.name,
        "Spend (R)": s.spend,
        "B-BBEE level": level_label(s.level),
        "Size": s.size,
        "Black ownership %": s.black_ownership_pct,
        "Black women ownership %": s.black_women_ownership_pct,
        "Designated group": s.designated_group,
        "Empowering supplier": s.empowering,
        "TMPS exclusion": EXCLUSIONS[s.exclusion],
    }


def to_csv(suppliers: Iterable[Supplier]) -> str:
    """Export a validated list in the template's format (re-uploads cleanly)."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(label for _, label in COLUMNS)
    for s in suppliers:
        r = to_record(s)
        w.writerow(
            [
                r["Supplier"],
                f"{s.spend:.2f}",
                r["B-BBEE level"],
                r["Size"],
                f"{s.black_ownership_pct:g}",
                f"{s.black_women_ownership_pct:g}",
                "yes" if s.designated_group else "no",
                "yes" if s.empowering else "no",
                s.exclusion,
            ]
        )
    return buf.getvalue()


def template_csv() -> str:
    """The downloadable template: headers plus illustrative rows (delete before use)."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(label for _, label in COLUMNS)
    w.writerows(TEMPLATE_ROWS)
    return buf.getvalue()


# ------------------------------------------------------------------------------ summary


def rand(amount: float) -> str:
    """South African display format: R1 250 000."""
    return f"R{amount:,.0f}".replace(",", " ")


def summarise(suppliers: Iterable[Supplier]) -> ProcurementSummary:
    suppliers = list(suppliers)
    excluded: dict[str, float] = {}
    recognised = dict.fromkeys(METRICS, 0.0)
    total = no_cert = non_emp = 0.0
    for s in suppliers:
        total += s.spend
        if s.excluded:
            excluded[s.exclusion] = excluded.get(s.exclusion, 0.0) + s.spend
            continue
        if not s.empowering:
            non_emp += s.spend
            continue
        if s.level == NON_COMPLIANT:
            no_cert += s.spend
        rec = s.recognised_spend
        for m in s.metrics():
            recognised[m] += rec
    tmps = total - sum(excluded.values())
    notes = []
    if suppliers and tmps <= 0:
        notes.append("TMPS is zero: every line is excluded, so no procurement points apply.")
    if no_cert:
        notes.append(
            f"{rand(no_cert)} of TMPS is with suppliers with no valid certificate or affidavit "
            "(0% recognition). Collecting these lifts every procurement measure."
        )
    if non_emp:
        notes.append(
            f"{rand(non_emp)} of TMPS is with suppliers that are not Empowering Suppliers "
            "and counts towards none of the procurement measures."
        )
    return ProcurementSummary(
        suppliers=len(suppliers),
        total_spend=total,
        excluded=excluded,
        tmps=tmps,
        recognised=recognised,
        no_certificate_spend=no_cert,
        non_empowering_spend=non_emp,
        notes=notes,
    )
