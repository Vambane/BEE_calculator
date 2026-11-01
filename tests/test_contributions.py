"""ED / SD / SED contributions valued at the gazetted benefit factors."""

import pytest

from bee import calculate
from bee.contributions import TYPES, factor, parse_rows, summarise, targets
from bee.models import CompanyProfile, Financials, Rand, ScoreInput
from bee.models import EnterpriseSize as S
from bee.registry import SECTORS, get_scorecard

GEN = get_scorecard(S.GENERIC)
SD, ED, SED = (t for t in targets(GEN))


def line(indicator, type_, amount, a=None, b=None, who="X"):
    return {
        "Beneficiary": who,
        "Counts towards": indicator,
        "Contribution type": TYPES[type_][0],
        "Amount (R)": amount,
        "Prime / ordinary rate %": a,
        "Actual rate %": b,
    }


@pytest.mark.parametrize(
    "type_, esd, sed",
    [
        ("grant", 100, 100),
        ("direct_cost", 100, 100),
        ("discount", 100, 100),
        ("overhead", 70, 80),
        ("interest_free_loan", 70, None),
        ("standard_loan", 50, None),
        ("guarantee", 50, None),  # GG 42496 (2019)
        ("minority_equity", 70, None),
        ("prof_free", 60, 80),
        ("prof_discount", 60, 80),
        ("employee_time", 60, 80),
    ],
)
def test_gazetted_factors(type_, esd, sed):
    assert factor(type_, SD, "generic") == esd
    if sed is None:
        with pytest.raises(ValueError, match="not an SED contribution"):
            factor(type_, SED, "generic")
    else:
        assert factor(type_, SED, "generic") == sed


def test_guarantee_uses_2013_factor_off_the_generic_card():
    qse = get_scorecard(S.QSE)
    assert factor("guarantee", targets(qse)[0], "qse") == 3


def test_rate_types():
    assert factor("lower_interest", ED, "generic", (11.75, 5)) == pytest.approx(6.75)
    assert factor("lower_dividend", ED, "generic", (12, 12)) == 0
    with pytest.raises(ValueError, match="both rates"):
        factor("lower_interest", ED, "generic", (11.75, None))
    with pytest.raises(ValueError, match="no benefit"):
        factor("lower_interest", ED, "generic", (5, 11.75))
    with pytest.raises(ValueError, match="not an SED"):
        factor("lower_interest", SED, "generic", (11.75, 5))


def test_hand_worked_summary_and_engine_points():
    """NPAT R10m. SD: R200k interest-free loan -> R140k (1.4%, 7 of 10 pts) plus R60k grant
    -> R200k (2%, 10 pts). ED: R1m at 5% vs prime 11.75% -> R67 500 (0.675%, 3.375 pts).
    SED: R125k staff time at 80% -> R100k (1%, 5 pts)."""
    rows = [
        line(SD.label, "interest_free_loan", 200_000),
        line(SD.label, "grant", 60_000),
        line(ED.label, "lower_interest", 1_000_000, 11.75, 5),
        line(SED.label, "employee_time", 125_000),
    ]
    lines, errors = parse_rows(rows, GEN)
    assert errors == []
    s = summarise(lines, GEN)
    assert s.by_clause == pytest.approx(
        {"400 2.2.1": 200_000, "400 2.3.1": 67_500, "500 2.1": 100_000}
    )
    assert s.gross_by_clause["400 2.2.1"] == 260_000
    assert s.percent_of("400 2.2.1", 10_000_000) == pytest.approx(2)
    assert s.percent_of("400 2.2.1", 0) is None
    r = calculate(
        ScoreInput(
            CompanyProfile(200e6, 0),
            financials=Financials(npat=10_000_000),
            indicators={
                "esd": {c: Rand(v) for c, v in s.by_clause.items() if c.startswith("400")},
                "sed": {"500 2.1": Rand(s.by_clause["500 2.1"])},
            },
        )
    )
    assert r.group_points["esd"]["sd"] == pytest.approx(10)
    assert r.group_points["esd"]["ed"] == pytest.approx(3.375)
    assert r.element_points["sed"] == pytest.approx(5)


def test_element_filter_and_clause_or_name_accepted():
    rows = [line("400 2.2.1", "grant", 1), line(SED.label, "grant", 1)]
    lines, errors = parse_rows(rows, GEN, "esd")
    assert len(lines) == 1 and len(errors) == 1 and errors[0].column == "Counts towards"


def test_single_target_element_defaults_the_indicator():
    lines, errors = parse_rows([line("", "grant", 10)], GEN, "sed")
    assert errors == [] and lines[0].clause == "500 2.1"


def test_errors_reported_per_row():
    rows = [
        {"Counts towards": SD.label, "Contribution type": "Bribe", "Amount (R)": 1},
        {"Counts towards": SD.label, "Contribution type": "Grant", "Amount (R)": -1},
        {"Counts towards": SD.label, "Contribution type": "Grant"},
        line(ED.label, "lower_interest", 10, 120, 5),
        {"Beneficiary": None, "Amount (R)": float("nan")},  # blank editor row: skipped
    ]
    lines, errors = parse_rows(rows, GEN)
    assert lines == []
    assert [(e.row, e.column) for e in errors] == [
        (1, "Contribution type"),
        (2, "Amount (R)"),
        (3, "Amount (R)"),
        (4, "Prime / ordinary rate %"),
    ]


def test_sector_notes():
    con = SECTORS["construction"].card(S.GENERIC, "contractor")
    t = targets(con, "esd")[0]
    lines, _ = parse_rows([line(t.label, "guarantee", 100)], con, "esd")
    s = summarise(lines, con)
    assert s.by_clause[t.indicator.clause] == pytest.approx(3)
    assert any("3%" in n for n in s.notes) and any("UNVERIFIED" in n for n in s.notes)


def test_every_card_with_contribution_indicators_has_targets():
    for cfg in SECTORS.values():
        for card in cfg.cards.values():
            for el in card.elements:
                if el.key in ("esd", "sed") and any(
                    i.base == "npat" and not i.bonus and not i.draft_only for i in el.indicators
                ):
                    assert targets(card, el.key), card.key
