"""Acceptance tests TC1-TC20 from bee-team/compliance/test-cases.md (revised 23 Oct 2026).

Where a test case gives only an element total, the sub-element breakdown chosen here is
noted in the case and is consistent with the case's stated pass/fail conditions.
"""

import pytest
from conftest import generic_points as gp
from conftest import make

from bee import EnterpriseSize, Financials, Rand, YesTier, calculate
from bee.indicators import element_group_points
from bee.registry import get_scorecard

GEN = 60_000_000
NC = 9

CASES = [
    # id, input, expected level, expected recognition %
    ("TC1", make(4_000_000, bo=100), 1, 135),
    ("TC2", make(10_000_000, bo=60), 2, 125),
    ("TC3", make(2_000_000, bo=30), 4, 100),
    # TC4 ESD 22 split as PP 14 / SD 4 / ED 4.
    ("TC4", make(10_000_001, points=gp(20, 6, 10, 18, 14, 4, 4, 5)), 5, 80),
    ("TC5", make(30_000_000, bo=100), 1, 135),
    ("TC7", make(GEN, points=gp(22, 5, 14, 15, 20, 8, 4, 5)), 4, 100),
    # TC8 ESD 35 split as PP 22 / SD 8 / ED 5; NV 5.
    ("TC8", make(GEN, points=gp(20, 5, 15, 6, 22, 8, 5, 5)), 5, 80),
    # TC9 82 = 22+15+6+(27+6+1)+5; SD 6 and ED 1 fail.
    ("TC9", make(GEN, points=gp(22, 5, 15, 6, 27, 6, 1, 5)), 5, 80),
    ("TC10", make(GEN, points=gp(23, 6, 17, 18, 22, 8, 4, 0), tier=YesTier.TARGET), 2, 125),
    ("TC11", make(GEN, points=gp(23, 6, 17, 18, 22, 8, 4, 1), tier=YesTier.TARGET_1_5X), 1, 135),
    # TC12 78; ED 1 fails; priority ratios .75/.80/.69 -> average .75 >= 50%.
    ("TC12", make(GEN, points=gp(20, 6, 10, 16, 20, 8, 1, 3), tier=YesTier.TARGET_2X), 4, 100),
    # TC13 Skills 4/20 (20%) fails; ratios .30/.20/.55 -> average 35%; 69.1 -> L7 -> L8.
    ("TC13", make(GEN, points=gp(18, 2.4, 19, 4, 15, 5.1, 3, 5), tier=YesTier.TARGET), 8, 10),
    ("TC14", make(GEN, points=gp(10, 4, 3, 8, 11, 4, 2, 0)), NC, 0),
    ("TC15", make(GEN, points=gp(25, 8, 19, 20, 27, 10, 5, 5), tier=YesTier.TARGET_2X), 1, 135),
    ("TC16", make(GEN, points=gp(25, 8, 19, 20, 10.5, 4, 2, 4.5)), 5, 80),
    ("TC17", make(GEN, points=gp(25, 8, 19, 20, 10.8, 4, 2, 4.2)), 4, 100),
    # TC19 99 = 25+19+7+(42 + 1 ESD bonus)+5; Skills 7 < 8 fails; average .78 >= 50%.
    (
        "TC19",
        make(GEN, points=gp(25, 8, 19, 7, 27, 10, 5, 5, esd_bonus=1), tier=YesTier.TARGET_2X),
        1,
        135,
    ),
]


@pytest.mark.parametrize("tc,inp,level,rec", CASES, ids=[c[0] for c in CASES])
def test_level(tc, inp, level, rec):
    res = calculate(inp)
    assert (res.level, res.recognition_pct) == (level, rec)


def test_tc4_details():
    res = calculate(CASES[3][1])
    assert res.size == EnterpriseSize.QSE and res.total_points == 75 and not res.discounted


def test_tc6_generic_boundary():
    assert calculate(make(50_000_000, points=gp(0, 0, 0, 0, 0, 0, 0, 0))).size == "Generic"


def test_tc7_total():
    assert calculate(CASES[5][1]).total_points == 88


def test_tc9_two_failures_one_level():
    res = calculate(CASES[7][1])
    assert res.total_points == 82 and res.level_before_discount == 4
    assert sum(not c.passed for c in res.submin_checks) == 2


def test_tc11_yes_points():
    assert calculate(CASES[9][1]).total_points == 96


def test_tc12_path():
    res = calculate(CASES[10][1])
    assert res.total_points == 78 and res.level_before_discount == 5 and res.discounted
    assert res.yes_applied


def test_tc13_yes_blocked():
    res = calculate(CASES[11][1])
    assert res.discounted and not res.yes_applied and "2.1" in res.yes_blocked_reason


def test_tc16_tc17_pp_submin():
    pp16 = next(c for c in calculate(CASES[14][1]).submin_checks if c.group == "pp")
    pp17 = next(c for c in calculate(CASES[15][1]).submin_checks if c.group == "pp")
    assert pp16.required == pp17.required == 10.8
    assert not pp16.passed and pp17.passed


def test_tc18_qse_mc_max_15():
    mc = get_scorecard(EnterpriseSize.QSE).element("management")
    vals = {"602 3.1.1.1.1": 50, "602 3.1.1.1.2": 25, "602 3.1.1.2.1": 60, "602 3.1.1.2.2": 30}
    pts = element_group_points(mc, vals, Financials())
    assert pts["main"]["points"] == pytest.approx(15)
    assert mc.max_points() == 15


def test_tc19_path():
    res = calculate(CASES[16][1])
    assert res.total_points == 99 and res.level_before_discount == 2 and res.discounted


def test_tc20_draft_flag_off():
    inp = make(GEN)
    inp.financials = Financials(npat=10_000_000)
    inp.indicators = {
        "esd": {
            "draft400 2.4.1": Rand(300_000),
            "400 2.2.1": Rand(200_000),
            "400 2.3.1": Rand(100_000),
        }
    }
    res = calculate(inp)
    assert "tf" not in res.group_points["esd"]
    assert res.group_points["esd"]["sd"] == 10 and res.group_points["esd"]["ed"] == 5
    assert any("ignored" in n for n in res.notes)
