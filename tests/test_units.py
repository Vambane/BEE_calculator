import pytest
from conftest import generic_points as gp
from conftest import make

from bee import (
    CompanyProfile,
    EnterpriseSize,
    Financials,
    Rand,
    ScoreInput,
    YesInput,
    YesTier,
    calculate,
    levels,
    registry,
)
from bee.engine import max_points
from bee.indicators import indicator_points
from bee.registry import get_scorecard
from bee.sizing import classify


@pytest.mark.parametrize(
    "rev,size",
    [
        (0, "EME"),
        (10_000_000, "EME"),
        (10_000_001, "QSE"),
        (49_999_999, "QSE"),
        (50_000_000, "Generic"),
    ],
)
def test_classify(rev, size):
    assert classify(rev) == size


def test_negative_revenue():
    with pytest.raises(ValueError):
        classify(-1)


@pytest.mark.parametrize(
    "pts,lvl",
    [
        (111, 1),
        (100, 1),
        (99.99, 2),
        (95, 2),
        (90, 3),
        (80, 4),
        (75, 5),
        (70, 6),
        (55, 7),
        (40, 8),
        (39.99, 9),
    ],
)
def test_levels(pts, lvl):
    assert levels.level_from_points(pts) == lvl


def test_discount_and_uplift_bounds():
    assert levels.discount(8) == 9 and levels.discount(9) == 9
    assert levels.uplift(2, 2) == 1


def test_max_points():
    assert max_points(get_scorecard(EnterpriseSize.GENERIC)) == 111
    assert max_points(get_scorecard(EnterpriseSize.QSE)) == 100


def test_rand_equals_percentage():
    esd = get_scorecard(EnterpriseSize.GENERIC).element("esd")
    sd = next(i for i in esd.indicators if i.clause == "400 2.2.1")
    fin = Financials(npat=5_000_000)
    assert indicator_points(sd, Rand(50_000), fin) == indicator_points(sd, 1.0, fin) == 5


def test_rand_needs_positive_base():
    sd = get_scorecard(EnterpriseSize.GENERIC).element("esd").indicators[6]
    with pytest.raises(ValueError):
        indicator_points(sd, Rand(1), Financials(npat=0))


def test_indicator_capped_at_points():
    ind = get_scorecard(EnterpriseSize.GENERIC).element("sed").indicators[0]
    assert indicator_points(ind, 5.0, Financials()) == 5


def test_unknown_clause_rejected():
    inp = make(60_000_000)
    inp.indicators = {"sed": {"nope": 1}}
    with pytest.raises(KeyError):
        calculate(inp)


def test_group_points_capped():
    res = calculate(make(60_000_000, points={"sed": {"main": 50}}))
    assert res.element_points["sed"] == 5


def test_skills_bonus_excluded_from_submin():
    pts = gp(25, 8, 19, 7, 27, 10, 5, 5)
    pts["skills"]["bonus"] = 5
    res = calculate(make(60_000_000, points=pts))
    assert res.total_points == 103 and res.discounted and res.level == 2


def test_qse_ownership_plus_one():
    # Skills fails, ESD passes -> no discount for a QSE.
    pts = gp(20, 6, 10, 5, 14, 4, 4, 5)
    assert not calculate(make(20_000_000, points=pts)).discounted
    # Ownership NV fails -> discount.
    pts = gp(20, 3, 10, 18, 14, 4, 4, 5)
    assert calculate(make(20_000_000, points=pts)).discounted


def test_qse_black_owned_opt_scored():
    inp = ScoreInput(
        profile=CompanyProfile(20_000_000, 60, opt_scored=True),
        points=gp(10, 4, 5, 10, 8, 2, 2, 0),
    )
    res = calculate(inp)
    assert not res.deemed and res.total_points == 37 and res.level == 9


def test_eme_opt_scored_uses_qse_card():
    inp = ScoreInput(
        profile=CompanyProfile(5_000_000, 0, opt_scored=True), points=gp(25, 8, 15, 25, 20, 5, 5, 5)
    )
    res = calculate(inp)
    assert res.size == EnterpriseSize.EME and res.total_points == 100 and res.level == 1


def test_eme_yes_uplift():
    res = calculate(make(2_000_000, bo=0, tier=YesTier.TARGET))
    assert res.deemed and res.level == 3


def test_yes_previous_level_block():
    inp = make(60_000_000, points=gp(23, 6, 17, 18, 22, 8, 4, 0))
    inp.yes = YesInput(YesTier.TARGET, previous_level=2)
    res = calculate(inp)
    assert res.level == 3 and not res.yes_applied


def test_draft_tf_route():
    inp = make(60_000_000, draft_rules=True)
    inp.financials = Financials(npat=10_000_000)
    inp.indicators = {"esd": {"draft400 2.4.1": Rand(300_000), "400 2.2.1": Rand(200_000)}}
    res = calculate(inp)
    g = res.group_points["esd"]
    assert g["tf"] == 20 and g["sd"] == 0
    assert {(c.group, c.required) for c in res.submin_checks if c.element == "esd"} == {
        ("pp", 10.8),
        ("tf", 8),
    }


def test_registry_sector():
    with pytest.raises(KeyError):
        get_scorecard(EnterpriseSize.GENERIC, "no-such-sector")
    card = get_scorecard(EnterpriseSize.GENERIC)
    registry.register("test-sector", EnterpriseSize.GENERIC, card)
    assert get_scorecard(EnterpriseSize.GENERIC, "TEST-SECTOR") is card
    res = calculate(ScoreInput(CompanyProfile(60_000_000, sector="test-sector")))
    assert res.sector == "test_sector"


def test_draft_esd_bonus_2_each():
    def run(draft):
        inp = make(60_000_000, draft_rules=draft)
        inp.indicators = {"esd": {"400 2.4.1": True, "400 2.4.2": True}}
        return calculate(inp).element_points["esd"]

    assert run(False) == 2 and run(True) == 4


def test_qse_bonuses_verified():
    card = get_scorecard(EnterpriseSize.QSE)
    esd = {i.clause: i for i in card.element("esd").indicators}
    assert esd["604 5.1.1.5.1"].points == esd["604 5.1.1.5.2"].points == 1
    assert (esd["604 5.1.1.2"].points, esd["604 5.1.1.2"].target) == (1, 1)
    assert card.element("sed").indicators[0].clause == "605 6.2"
    assert not any("UNVERIFIED" in i.name for e in card.elements for i in e.indicators)


def test_interpretation_notes():
    inp = make(60_000_000, points=gp(23, 6, 17, 18, 22, 8, 4, 0), tier=YesTier.TARGET)
    notes = " ".join(calculate(inp).notes)
    assert "INTERPRETATION" in notes and "Annexe 100" in notes


def test_yes_1_5x_points_removed_when_previous_level_not_maintained():
    # QA B1: 87 pts, YES 1.5x, previous level L1 -> no +3, no uplift -> L4.
    pts = {
        "ownership": {"main": 17, "net_value": 8},
        "management": {"main": 17},
        "skills": {"main": 18},
        "esd": {"pp": 18, "sd": 6, "ed": 3},
        "sed": {"main": 0},
    }
    res = calculate(
        ScoreInput(
            profile=CompanyProfile(60_000_000, 0),
            points=pts,
            yes=YesInput(YesTier.TARGET_1_5X, previous_level=1),
        )
    )
    assert res.total_points == 87
    assert res.level == 4
    assert not res.yes_applied
    assert "2.4" in res.yes_blocked_reason
