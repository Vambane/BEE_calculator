"""Annexe 100(E) Net Value: Formula A (graduated, debt-adjusted) vs Formula B (econ. interest)."""

from datetime import date

import pytest

from bee.net_value import (
    DEFAULT_TARGET,
    GRADUATION,
    NetValueInput,
    calculate,
    graduation_factor,
    measurement_year,
    validate,
)


def nv(b=200_000.0, c=50_000.0, d=1_000_000.0, e=20.0, year=3, w=8.0, t=DEFAULT_TARGET):
    return NetValueInput(b, c, d, e, year, w, t)


# ------------------------------------------------------------------ graduation factor
@pytest.mark.parametrize(
    ("year", "factor"),
    [
        (1, 0.10),
        (2, 0.20),
        (3, 0.40),
        (4, 0.40),
        (5, 0.60),
        (6, 0.60),
        (7, 0.80),
        (8, 0.80),
        (9, 1.00),
        (10, 1.00),
        (11, 1.00),
        (30, 1.00),
    ],
)
def test_graduation_table(year, factor):
    assert graduation_factor(year) == factor


def test_graduation_never_decreases():
    vals = [GRADUATION[y] for y in sorted(GRADUATION)]
    assert vals == sorted(vals)


def test_graduation_rejects_year_zero():
    with pytest.raises(ValueError):
        graduation_factor(0)


@pytest.mark.parametrize(
    ("start", "end", "year"),
    [
        (date(2020, 3, 1), date(2020, 3, 1), 1),
        (date(2020, 3, 1), date(2021, 2, 28), 1),
        (date(2020, 3, 1), date(2021, 3, 1), 2),
        (date(2020, 2, 29), date(2021, 2, 28), 1),
        (date(2020, 2, 29), date(2021, 3, 1), 2),
        (date(2014, 5, 1), date(2025, 6, 30), 12),
    ],
)
def test_measurement_year(start, end, year):
    assert measurement_year(start, end) == year


def test_measurement_before_equity_date_rejected():
    with pytest.raises(ValueError, match="before"):
        measurement_year(date(2024, 1, 1), date(2023, 12, 31))


# ------------------------------------------------------------------ formulas
def test_worked_example_formula_b_binds():
    # R1m company, R200k black shares (20% EI), R50k debt, year 3 (F = 40%).
    r = calculate(nv())
    assert r.deemed_value_pct == pytest.approx(15.0)
    assert r.required_pct == pytest.approx(10.0)
    assert r.points_a == 8.0  # 15 / 10 x 8 = 12, capped
    assert r.points_b == pytest.approx(6.4)  # 20 / 25 x 8
    assert r.points == pytest.approx(6.4)
    assert r.binding == "B"
    assert r.pct_of_target == pytest.approx(80.0)
    assert any("capped at 8" in n for n in r.notes)


def test_debt_heavy_deal_formula_a_binds():
    # 51% sold on a R51m loan with R36m still owed, company R100m, year 9 (F = 100%).
    r = calculate(nv(b=51e6, c=36e6, d=100e6, e=51.0, year=9))
    assert r.points_a == pytest.approx(15 / 25 * 8)  # 4.8
    assert r.points_b == 8.0
    assert r.points == pytest.approx(4.8)
    assert r.binding == "A"


def test_same_deal_scores_higher_early_because_of_graduation():
    early = calculate(nv(b=51e6, c=36e6, d=100e6, e=51.0, year=1))
    late = calculate(nv(b=51e6, c=36e6, d=100e6, e=51.0, year=9))
    assert early.points == 8.0 > late.points


def test_debt_exceeding_equity_scores_zero_on_a():
    r = calculate(nv(b=100_000.0, c=150_000.0, e=10.0))
    assert r.deemed_value_pct == 0
    assert r.points_a == 0
    assert r.points == 0
    assert any("nil" in n for n in r.notes)


def test_no_black_ownership_scores_zero():
    r = calculate(nv(b=0.0, c=0.0, e=0.0))
    assert r.points == 0 and r.binding == "A and B"


def test_both_formulas_capped_at_weighting():
    r = calculate(nv(b=1e6, c=0.0, d=1e6, e=100.0, year=10))
    assert r.points == 8.0 and r.binding == "A and B"


@pytest.mark.parametrize("w", [5.0, 6.0, 8.0])
def test_sector_weightings_scale_and_cap(w):
    r = calculate(nv(w=w, year=9, c=0.0, b=100_000.0, e=10.0))  # 10% vs 25% target
    assert r.points == pytest.approx(0.4 * w)
    assert r.pct_of_target == pytest.approx(40.0)


def test_custom_target():
    r = calculate(nv(b=300_000.0, c=0.0, e=30.0, year=9, t=30.0))
    assert r.points == pytest.approx(8.0)


def test_sub_minimum_boundary_at_40_percent():
    # Exactly 10% unencumbered against a 25% target in year 9: 3.2 points.
    r = calculate(nv(b=100_000.0, c=0.0, e=10.0, year=9))
    assert r.points == pytest.approx(3.2)


def test_deemed_above_economic_interest_flagged():
    r = calculate(nv(b=300_000.0, c=0.0, e=10.0))
    assert any("higher than the economic interest" in n for n in r.notes)


# ------------------------------------------------------------------ validation
def test_validation_reports_every_problem():
    errs = validate(NetValueInput(-1.0, -1.0, 0.0, 120.0, 0, 0.0, 0.0))
    assert len(errs) == 7


def test_equity_worth_more_than_entity_rejected():
    with pytest.raises(ValueError, match="more than the whole entity"):
        calculate(nv(b=2e6, d=1e6))
