"""Statement 400 cl. 3.2.1: NPAT targets on a Turnover basis for a loss or low margin."""

import pytest

from bee import calculate
from bee.models import CompanyProfile, Financials, Rand, ScoreInput
from bee.npat import resolve

REV = 200_000_000


def test_profitable_entity_keeps_npat():
    b = resolve(REV, 20_000_000, industry_norm_pct=8)
    assert (b.npat, b.deemed, b.reasons) == (20_000_000, False, ())


def test_no_npat_given_is_not_deemed():
    assert resolve(REV, None) == resolve(REV, None, None, None, None)
    assert resolve(REV, None).npat is None and not resolve(REV, None).deemed


@pytest.mark.parametrize(
    "npat, avg5, reason",
    [
        (-5_000_000, None, "no profit last year"),
        (10_000_000, -1, "no profit on average over five years"),
        (1_000_000, None, "below a quarter"),  # 0.5% margin < 2% (a quarter of 8%)
    ],
)
def test_each_trigger_switches_to_turnover_basis(npat, avg5, reason):
    b = resolve(REV, npat, avg5, industry_norm_pct=8, qualifying_margin_pct=4)
    assert b.deemed and any(reason in r for r in b.reasons)
    assert b.npat == pytest.approx(0.04 * REV)  # Indicative Profit Margin x Turnover
    assert not b.interpretation


def test_margin_exactly_a_quarter_of_norm_is_not_low():
    b = resolve(REV, 0.02 * REV, industry_norm_pct=8)
    assert not b.deemed


def test_fallback_to_quarter_of_norm_is_flagged_interpretation():
    b = resolve(REV, -1, industry_norm_pct=8)
    assert b.npat == pytest.approx(0.02 * REV) and b.interpretation
    assert "INTERPRETATION" in b.note(REV)


def test_deemed_needed_but_no_margin_or_norm():
    b = resolve(REV, -1)
    assert b.deemed and b.npat is None and "industry norm" in b.problem


def test_zero_turnover_cannot_use_turnover_basis():
    b = resolve(0, -1, industry_norm_pct=8)
    assert b.deemed and b.npat is None and "Turnover" in b.problem


@pytest.mark.parametrize(
    "kw, msg",
    [
        ({"industry_norm_pct": 0}, "Industry norm"),
        ({"industry_norm_pct": 120}, "Industry norm"),
        ({"qualifying_margin_pct": float("nan")}, "Qualifying margin"),
        ({"npat_avg_5y": float("inf")}, "Five-year"),
        ({"industry_norm_pct": 8, "qualifying_margin_pct": 1}, "at least a quarter"),
    ],
)
def test_invalid_inputs_raise(kw, msg):
    with pytest.raises(ValueError, match=msg):
        resolve(REV, -1, **kw)


def _score(fin, esd=None, sed=None):
    ind = {"esd": esd or {}, "sed": sed or {}}
    return calculate(ScoreInput(CompanyProfile(REV, 0), financials=fin, indicators=ind))


def test_engine_scores_loss_maker_against_deemed_npat():
    """R8m deemed NPAT: R160k SD = 2% (10 pts), R80k ED = 1% (5), R80k SED = 1% (5)."""
    fin = Financials(npat=-5_000_000, industry_norm_margin_pct=8, qualifying_margin_pct=4)
    r = _score(
        fin,
        {"400 2.2.1": Rand(160_000), "400 2.3.1": Rand(80_000)},
        {"500 2.1": Rand(80_000)},
    )
    assert r.group_points["esd"]["sd"] == pytest.approx(10)
    assert r.group_points["esd"]["ed"] == pytest.approx(5)
    assert r.element_points["sed"] == pytest.approx(5)
    assert any("Turnover basis (cl. 3.2.1" in n for n in r.notes)


def test_engine_leaves_profitable_entity_alone():
    r = _score(
        Financials(npat=20_000_000, industry_norm_margin_pct=8), {"400 2.2.1": Rand(200_000)}
    )
    assert r.group_points["esd"]["sd"] == pytest.approx(5)  # 1% of 20m vs 2% target
    assert not any("3.2.1" in n for n in r.notes)


def test_engine_loss_without_basis_rejects_rand_amounts():
    with pytest.raises(ValueError, match="npat must be > 0"):
        _score(Financials(npat=-5_000_000), {"400 2.2.1": Rand(1)})
