"""Procurement calculator: supplier list -> TMPS -> % of TMPS per indicator -> points."""

from pathlib import Path

import pytest

from bee import calculate
from bee.models import CompanyProfile, Financials, Rand, ScoreInput
from bee.models import EnterpriseSize as S
from bee.procurement import (
    COLUMNS,
    METRICS,
    Supplier,
    classify_indicator,
    parse_csv,
    parse_rows,
    procurement_indicators,
    summarise,
    template_csv,
    to_csv,
    to_record,
)
from bee.registry import SECTORS, get_scorecard

# Hand-worked example (R):
#   A  1 000 000  L1 (135%)  QSE    100% BO, 60% BWO            -> 1 350 000
#   B    500 000  L4 (100%)  EME     30% BO                     ->   500 000
#   C    400 000  L2 (125%)  Large   51% BO, 30% BWO, designated ->  500 000
#   D    600 000  no cert    Unknown                            ->         0
#   E    200 000  L1, not an Empowering Supplier                ->         0
#   F    300 000  tax (excluded from TMPS)
# Total 3 000 000; excluded 300 000; TMPS 2 700 000.
SUPPLIERS = [
    Supplier("A", 1_000_000, 1, "QSE", 100, 60),
    Supplier("B", 500_000, 4, "EME", 30, 0),
    Supplier("C", 400_000, 2, "Large", 51, 30, designated_group=True),
    Supplier("D", 600_000, 9, "Unknown"),
    Supplier("E", 200_000, 1, "Large", 0, 0, empowering=False),
    Supplier("F", 300_000, 9, "Unknown", exclusion="tax"),
]
TMPS = 2_700_000


def pct(rand):
    return rand / TMPS * 100


def test_tmps_and_recognised_spend_by_hand():
    s = summarise(SUPPLIERS)
    assert s.total_spend == 3_000_000
    assert s.excluded == {"tax": 300_000}
    assert s.tmps == TMPS
    assert s.recognised == {
        "all": 2_350_000,
        "qse": 1_350_000,
        "eme": 500_000,
        "bo51": 1_850_000,
        "bwo30": 1_850_000,
        "bwo35": 1_350_000,
        "bwo51": 1_350_000,
        "designated": 500_000,
    }
    assert s.no_certificate_spend == 600_000
    assert s.non_empowering_spend == 200_000
    assert s.percent("all") == pytest.approx(pct(2_350_000))


def test_generic_indicator_values_and_points():
    card = get_scorecard(S.GENERIC)
    s = summarise(SUPPLIERS)
    values, unmatched = s.indicator_values(card.element("esd"))
    assert unmatched == []
    assert values == pytest.approx(
        {
            "400 2.1.1": pct(2_350_000),
            "400 2.1.2": pct(1_350_000),
            "400 2.1.3": pct(500_000),
            "400 2.1.4": pct(1_850_000),
            "400 2.1.5": pct(1_850_000),
            "400 2.1.6": pct(500_000),
        },
        abs=1e-3,
    )
    r = calculate(ScoreInput(CompanyProfile(100e6, 0), indicators={"esd": values}))
    # Every measure is at or above target: full PP (27) plus the designated-group bonus (2).
    assert r.group_points["esd"]["pp"] == pytest.approx(27)
    assert r.element_points["esd"] == pytest.approx(29)


def test_qse_card_uses_only_its_two_measures():
    card = get_scorecard(S.QSE)
    values, unmatched = summarise(SUPPLIERS).indicator_values(card.element("esd"))
    assert set(values) == {"604 5.1.1.1.1", "604 5.1.1.1.2", "604 5.1.1.2"}
    assert unmatched == []


def test_applied_rand_amount_is_exact():
    """No rounding drift: % of TMPS x TMPS gives back the recognised rand amount."""
    s = summarise(SUPPLIERS)
    values, _ = s.indicator_values(get_scorecard(S.GENERIC).element("esd"))
    assert values["400 2.1.1"] * s.tmps / 100 == pytest.approx(2_350_000, abs=1e-6)


def test_rand_mode_equivalent_to_percentages():
    """Applying in rand mode (pct x TMPS) scores the same as applying percentages."""
    card = get_scorecard(S.GENERIC)
    values, _ = summarise(SUPPLIERS).indicator_values(card.element("esd"))
    as_pct = calculate(ScoreInput(CompanyProfile(100e6, 0), indicators={"esd": values}))
    as_rand = calculate(
        ScoreInput(
            CompanyProfile(100e6, 0),
            financials=Financials(tmps=TMPS),
            indicators={"esd": {k: Rand(v * TMPS / 100) for k, v in values.items()}},
        )
    )
    assert as_rand.element_points["esd"] == pytest.approx(as_pct.element_points["esd"])


@pytest.mark.parametrize(
    "level, expected",
    [(1, 135), (2, 125), (3, 110), (4, 100), (5, 80), (6, 60), (7, 50), (8, 10), (9, 0)],
)
def test_recognition_by_level(level, expected):
    assert Supplier("x", 1000, level).recognised_spend == pytest.approx(expected * 10)


def test_every_loaded_scorecard_procurement_indicator_is_matched():
    """One supplier list must feed every sector card, not just Generic."""
    seen = 0
    for cfg in SECTORS.values():
        for card in cfg.cards.values():
            for el in card.elements:
                for ind in procurement_indicators(el):
                    assert classify_indicator(ind) in METRICS, (card.key, ind.name)
                    seen += 1
    assert seen > 50


def test_ownership_thresholds_are_inclusive():
    assert "bo51" in Supplier("x", 1, 1, black_ownership_pct=51).metrics()
    assert "bo51" not in Supplier("x", 1, 1, black_ownership_pct=50.99).metrics()
    assert (
        "bwo30"
        in Supplier("x", 1, 1, black_ownership_pct=30, black_women_ownership_pct=30).metrics()
    )
    # Designated group needs the supplier to be at least 51% black owned as well.
    assert (
        "designated"
        not in Supplier("x", 1, 1, black_ownership_pct=40, designated_group=True).metrics()
    )


def test_excluded_and_non_empowering_count_nowhere():
    assert Supplier("x", 1, 1, exclusion="import").metrics() == ()
    assert Supplier("x", 1, 1, empowering=False).metrics() == ()


def test_all_excluded_gives_zero_tmps_without_dividing_by_zero():
    s = summarise([Supplier("x", 100, 1, exclusion="payroll")])
    assert s.tmps == 0
    assert s.percent("all") == 0
    assert any("TMPS is zero" in n for n in s.notes)


def test_empty_list():
    s = summarise([])
    assert (s.tmps, s.suppliers, s.notes) == (0, 0, [])


# ------------------------------------------------------------------------------ parsing


def test_parse_accepts_spreadsheet_formats():
    rows = [
        {
            "Supplier": "Acme",
            "Spend (R)": "R1 250 000,00".replace(",00", ".00"),
            "B-BBEE level": "Level 2",
            "Size": "qse",
            "Black ownership %": "51%",
            "Black women ownership %": "",
            "Designated group": "Y",
            "Empowering supplier": "",
            "TMPS exclusion": "",
        },
        {
            "supplier": "Beta",
            "spend": "1,000",
            "level": "NC",
            "size": "",
            "exclusion": "Taxes, levies and duties",
        },
        {"supplier": "Gamma", "spend": 10, "level": 8.0, "size": "generic"},
        {"supplier": "", "spend": "", "level": ""},  # blank row skipped
    ]
    suppliers, errors = parse_rows(rows)
    assert errors == []
    a, b, g = suppliers
    assert (a.spend, a.level, a.size, a.black_ownership_pct, a.designated_group, a.empowering) == (
        1_250_000,
        2,
        "QSE",
        51,
        True,
        True,
    )
    assert (b.spend, b.level, b.size, b.exclusion) == (1000, 9, "Unknown", "tax")
    assert (g.level, g.size) == (8, "Large")


def test_parse_reports_every_problem_with_row_numbers():
    rows = [
        {"supplier": "A", "spend": "-5", "level": "11", "size": "big"},
        {"supplier": "B", "spend": "abc", "level": "3", "black_ownership_pct": "120"},
        {
            "supplier": "C",
            "spend": "1",
            "level": "3",
            "black_ownership_pct": "20",
            "black_women_ownership_pct": "40",
        },
        {
            "supplier": "D",
            "spend": "1",
            "level": "3",
            "exclusion": "donation",
            "empowering": "maybe",
        },
    ]
    suppliers, errors = parse_rows(rows)
    assert suppliers == []
    got = {(e.row, e.column) for e in errors}
    assert got == {
        (1, "Spend (R)"),
        (1, "B-BBEE level"),
        (1, "Size"),
        (2, "Spend (R)"),
        (2, "Black ownership %"),
        (3, "Black women ownership %"),
        (4, "TMPS exclusion"),
        (4, "Empowering supplier"),
    }
    assert str(errors[0]).startswith("Row 1, Spend (R):")


def test_parse_handles_pandas_nan_cells():
    nan = float("nan")
    suppliers, errors = parse_rows(
        [
            {
                "Supplier": "A",
                "Spend (R)": 100.0,
                "B-BBEE level": "4",
                "Size": None,
                "Black ownership %": nan,
                "Black women ownership %": nan,
                "Designated group": False,
                "Empowering supplier": True,
                "TMPS exclusion": None,
            }
        ]
    )
    assert errors == [] and suppliers[0].black_ownership_pct == 0


def test_csv_missing_required_columns():
    _, errors = parse_csv("Name,Amount\nA,1\n")
    assert len(errors) == 1 and "missing column" in errors[0].message


def test_csv_semicolon_and_bom_and_extra_columns():
    text = "﻿Supplier;Spend (R);B-BBEE level;Notes\nA;1000;1;hello\n"
    suppliers, errors = parse_csv(text)
    assert errors == [] and suppliers[0].spend == 1000 and suppliers[0].level == 1


def test_template_parses_and_export_round_trips():
    suppliers, errors = parse_csv(template_csv())
    assert errors == [] and len(suppliers) == 3
    again, errors = parse_csv(to_csv(SUPPLIERS))
    assert errors == [] and again == SUPPLIERS


def test_editor_records_round_trip():
    again, errors = parse_rows([to_record(s) for s in SUPPLIERS])
    assert errors == [] and again == SUPPLIERS
    assert list(to_record(SUPPLIERS[0])) == [label for _, label in COLUMNS]


def test_docs_mention_the_calculator():
    howto = (Path(__file__).resolve().parent.parent / "docs" / "HOW_TO.md").read_text()
    assert "supplier list" in howto.lower()
