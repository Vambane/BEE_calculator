"""Full-scorecard v1.1: gender contribution helpers + Compliance acceptance checks."""

from bee import CompanyProfile, Financials, ScoreInput, calculate
from bee.models import EnterpriseSize as E
from bee.registry import get_sector
from bee.scorecards import generic, qse
from bee_ui.core import (
    default_entry_mode,
    gender_contribution,
    gender_indicators,
    gender_max_points,
    indicator_render_units,
    is_gender_indicator,
)


def test_generic_gender_y_is_14_not_hardcoded_qse():
    y = gender_max_points(generic.SCORECARD)
    assert y == 14.0  # Own 4 + MC 6 + PP 4; no Generic Skills women spend line


def test_qse_gender_y_is_15():
    y = gender_max_points(qse.SCORECARD)
    assert y == 15.0  # Own 4 + MC 4 + Skills 7; no QSE PP women-owned line


def test_generic_skills_has_no_women_spend_line():
    skills = generic.SCORECARD.element("skills")
    assert not any(is_gender_indicator(i) for i in skills.indicators)


def test_gender_contribution_x_from_indicators():
    card = generic.SCORECARD
    fin = Financials(tmps=100_000_000)
    inds = {
        "ownership": {
            "100 2.1.2": 10.0,  # full VR women -> 2 pts
            "100 2.2.2": 10.0,  # full EI women -> 2 pts
        },
        "management": {
            "200 2.1.2": 25.0,  # 1 pt
        },
        "esd": {
            "400 2.1.5": 12.0,  # full PP women-owned -> 4 pts
        },
    }
    x, y = gender_contribution(card, inds, fin)
    assert y == 14.0
    assert x == 2 + 2 + 1 + 4


def test_default_entry_indicators_for_ownership_mc_qse_skills():
    assert default_entry_mode(generic.SCORECARD.element("ownership")) == "ind"
    assert default_entry_mode(generic.SCORECARD.element("management")) == "ind"
    assert default_entry_mode(qse.SCORECARD.element("skills")) == "ind"
    # Generic Skills has no gender line — still ind-first via entry_options
    assert default_entry_mode(generic.SCORECARD.element("skills")) == "ind"


def test_ownership_pairs_include_women_clauses():
    units = indicator_render_units(generic.SCORECARD.element("ownership"), False)
    pairs = [u for u in units if u["kind"] == "pair"]
    women_clauses = {u["women"].clause for u in pairs}
    assert "100 2.1.2" in women_clauses
    assert "100 2.2.2" in women_clauses


def test_generic_mc_six_female_lines_in_pairs():
    units = indicator_render_units(generic.SCORECARD.element("management"), False)
    women = [u["women"].clause for u in units if u["kind"] == "pair"]
    for cl in (
        "200 2.1.2",
        "200 2.1.4",
        "200 2.2.2",
        "200 2.3.2",
        "200 2.4.2",
        "200 2.5.2",
    ):
        assert cl in women


def test_qse_ownership_mc_women_visible_in_units():
    for key, clauses in (
        ("ownership", ("601 2.1.1.2", "601 2.1.2.2")),
        ("management", ("602 3.1.1.1.2", "602 3.1.1.2.2")),
    ):
        units = indicator_render_units(qse.SCORECARD.element(key), False)
        women = {u["women"].clause for u in units if u["kind"] == "pair"}
        for cl in clauses:
            assert cl in women


def test_tourism_large_women_ownership_target_15():
    cfg = get_sector("tourism")
    card = cfg.card(E.GENERIC, None)
    women = [
        i
        for i in card.element("ownership").indicators
        if is_gender_indicator(i) and "owned" not in i.name.lower()
    ]
    assert women
    assert all(i.target == 15.0 for i in women)


def test_pp_women_owned_is_labelled_single_not_pair():
    units = indicator_render_units(generic.SCORECARD.element("esd"), False)
    owned = [u for u in units if u["kind"] == "single" and u.get("women_owned")]
    assert any("400 2.1.5" == u["ind"].clause for u in owned)


def test_eme_deemed_has_no_gender_metric_path():
    r = calculate(ScoreInput(CompanyProfile(5_000_000, 60)))  # EME deemed
    assert r.deemed
    # Contribution helpers still describe the QSE card when opted in:
    r2 = calculate(ScoreInput(CompanyProfile(5_000_000, 60, opt_scored=True)))
    assert not r2.deemed
    assert gender_max_points(qse.SCORECARD) > 0


def test_gender_indicators_list_generic():
    clauses = {i.clause for _, i in gender_indicators(generic.SCORECARD)}
    assert "100 2.1.2" in clauses and "400 2.1.5" in clauses
