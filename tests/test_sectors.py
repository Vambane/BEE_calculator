"""Sector acceptance tests from bee-team/compliance/sector-test-cases.md (23 Oct 2026) and
FS-D1 (rules-baseline.md decisions). Points breakdowns chosen for each case are inline."""

import pytest

from bee import CompanyProfile, EnterpriseSize, ScoreInput, YesInput, YesTier, calculate
from bee.registry import get_scorecard, get_sector
from bee.sectors import SectorExcludedError

G, Q, E = EnterpriseSize.GENERIC, EnterpriseSize.QSE, EnterpriseSize.EME


def run(sector, rev, bo=30.0, variant=None, points=None, options=None, tier=YesTier.NONE):
    return calculate(
        ScoreInput(
            CompanyProfile(rev, bo, sector=sector, variant=variant),
            points=points or {},
            options=options or {},
            yes=YesInput(tier),
        )
    )


def pts(own, nv, mc, sd, esd: dict, sed, **extra):
    d = {
        "ownership": {"total": own, "net_value": nv},
        "management": {"main": mc},
        "skills": {"main": sd},
        "esd": esd,
        "sed": {"main": sed},
    }
    d.update({k: {"main": v} for k, v in extra.items()})
    return d


FS_OTHER_OK = pts(25, 6, 20, 20, {"pp": 20, "sd": 10, "ed": 5}, 5)


def fs_other(**over):
    p = {k: dict(v) for k, v in FS_OTHER_OK.items()}
    for k, v in over.items():
        p[k].update(v)
    return p


# ----------------------------------------------------------------------- Construction
def test_con1_eme_under_30_is_l5():
    r = run("construction", 8_000_000, 20)
    assert (r.size, r.level, r.recognition_pct, r.deemed) == (E, 5, 80, True)


@pytest.mark.parametrize("bo,lvl", [(29.9, 5), (30, 4), (50, 4), (51, 2), (100, 1)])
def test_construction_eme_table(bo, lvl):
    assert run("construction", 8_000_000, bo).level == lvl


def test_con2_bep_r7m_is_qse():
    r = run("construction", 7_000_000, 30, "bep",
            {"ownership": {"main": 20}, "skills": {"main": 10}})
    assert r.size == Q and r.scorecard == "construction-qse"


def test_con3_pp_below_7_6_discounts_one_level():
    p = pts(27, 6, 18, 21,
            {"main": 15, "pp": 7.0, "sd_programmes": 2, "sd_contributions": 4}, 5)
    r = run("construction", 200_000_000, 30, "contractor", p)
    assert r.total_points == 99 and r.level_before_discount == 2
    assert r.discounted and r.level == 3
    assert [c.group for c in r.submin_checks if not c.passed] == ["pp"]


def test_con4_eme_skills_obligation():
    r = run("construction", 5_000_000, 40, options={"eme_skills_pct_of_qse_target": 30})
    assert (r.level, r.discounted) == (5, True)
    # start-up exemption
    r = run("construction", 5_000_000, 40,
            options={"eme_skills_pct_of_qse_target": 30, "start_up": True})
    assert r.level == 4


def test_construction_eme_enhancement():
    r = run("construction", 8_000_000, 40,
            options={"eme_full_skills_points": True, "eme_full_sd_points": True})
    assert r.level == 2


# ------------------------------------------------------------------ Financial Services
def test_fs1_bank_scorecard_total_120():
    card = get_scorecard(G, "financial", "bank")
    assert card.key == "fs-bank" and card.max_total() == 120
    assert run("financial", 2_000_000_000, variant="bank",
               points=pts(23, 6, 20, 20, {"main": 15}, 5, ef=25, afs=12)).level == 1


@pytest.mark.parametrize(
    "variant,total", [("bank", 120), ("short_term_insurer", 115), ("exchange", 103),
                      ("other", 105)]
)
def test_fs_scorecard_totals(variant, total):
    assert get_scorecard(G, "financial", variant).max_total() == total


def test_fs2_normalised_to_109():
    p = pts(20, 5, 18, 18, {"pp": 15, "sd": 8, "ed": 4}, 5, afs=4)
    r = run("financial", 500_000_000, variant="short_term_insurer", points=p)
    assert r.total_points == 92
    assert r.level_points == pytest.approx(87.2, abs=0.01) and r.level == 4
    off = run("financial", 500_000_000, variant="short_term_insurer", points=p,
              options={"fs_rescale_109": False})
    assert off.level_points == 92 and off.level == 3


def test_fs3_qsfi_esd_fails_no_discount():
    p = pts(20, 4, 10, 15, {"pp": 5, "sd": 1, "ed": 1}, 5)
    r = run("financial", 30_000_000, 30, points=p)
    assert r.size == Q and r.scorecard == "fs-qsfi" and not r.discounted


def test_fs4_other_pp_7_5_discounted():
    r = run("financial", 100_000_000, variant="other",
            points=fs_other(esd={"pp": 7.5}))
    assert r.level_before_discount == 2 and r.discounted and r.level == 3


def test_fs_d1_skills_submin_default_8_with_note():
    r = run("financial", 100_000_000, variant="other", points=fs_other(skills={"main": 7}))
    chk = next(c for c in r.submin_checks if c.element == "skills")
    assert chk.required == 8 and not chk.passed and r.discounted
    assert any("FS-D1" in w for w in r.warnings)
    assert any("Interpretation" in n and "fs_skills_submin" in n for n in r.notes)


def test_fs_skills_submin_option_6():
    r = run("financial", 100_000_000, variant="other", points=fs_other(skills={"main": 7}),
            options={"fs_skills_submin": 6})
    assert not r.discounted


# ----------------------------------------------------------------------------- AgriBEE
def test_ag1_qse_scorecard():
    card = get_scorecard(Q, "agri")
    assert [e.max_points() for e in card.elements] == [25, 15, 30, 25, 15]
    assert run("agri", 30_000_000, 30, points=pts(20, 5, 10, 20, {"main": 20}, 10)).size == Q


def test_ag2_r10m_is_eme_with_warning():
    r = run("agri", 10_000_000, 30)
    assert r.size == E and any("cl. 2.7" in w for w in r.warnings)


def test_ag3_silent_esd_submin_40pct():
    r = run("agri", 100_000_000, 30,
            points=pts(25, 8, 19, 20, {"main": 15}, 15))
    chk = next(c for c in r.submin_checks if c.element == "esd")
    assert chk.required == 16 and not chk.passed and r.discounted


def test_agri_large_total_119():
    assert get_scorecard(G, "agri").max_total() == 119


# ----------------------------------------------------------------------------- Tourism
def test_to1_qse_60pct_auto_l2():
    r = run("tourism", 40_000_000, 60)
    assert (r.size, r.level, r.deemed) == (Q, 2, True)


def test_to2_r45m_is_large():
    assert run("tourism", 45_000_000, points=pts(0, 0, 0, 0, {}, 0)).size == G


def test_to3_nv_3_0_discounted():
    p = pts(27, 3.0, 19, 20, {"pp": 25, "sd": 10, "ed": 5}, 5)
    r = run("tourism", 100_000_000, points=p)
    assert r.total_points == 111 and r.discounted and r.level == 2


def test_tourism_totals():
    assert get_scorecard(G, "tourism").max_total() == 111
    assert get_scorecard(Q, "tourism").max_total() == 101


# --------------------------------------------------------------------------------- ICT
def test_ict1_eme_deemed_l4_unverified_warning():
    r = run("ict", 9_000_000, 30)
    assert (r.size, r.level) == (E, 4)
    assert get_sector("ict").status == "unverified"
    assert any(w.startswith("UNVERIFIED") for w in r.warnings)


def test_ict2_skills_below_40pct_discounted():
    p = pts(25, 8, 23, 7, {"pp": 25, "sd": 10, "ed": 15}, 12)
    r = run("ict", 100_000_000, points=p)
    assert r.level_before_discount == 1 and r.discounted and r.level == 2


# --------------------------------------------------------------------------------- MAC
@pytest.mark.parametrize("tc,rev", [("MAC-1", 12_000_000), ("MAC-2", 30_000_000)])
def test_mac_excluded(tc, rev):
    """MAC-1/MAC-2 expected sizing results; MAC is excluded by owner decision, so the
    engine refuses with a warning instead (not a spec inconsistency)."""
    with pytest.raises(SectorExcludedError, match="excluded"):
        run("mac", rev)


# ---------------------------------------------------------------- fallback sectors
FALLBACK = ["property", "defence", "forestry", "chartered_accountancy", "legal", "transport"]


@pytest.mark.parametrize("sector", FALLBACK)
def test_pr1_ot1_tr2_fallback_generic_with_warning(sector):
    r = run(sector, 100_000_000, points=pts(22, 5, 14, 15, {"pp": 20, "sd": 8, "ed": 4}, 5))
    assert r.scorecard == "generic" and r.level == 4
    assert any("not loaded" in w for w in r.warnings)


def test_pr2_property_submin_40pct_of_weighting():
    r = run("property", 100_000_000, points=pts(0, 0, 0, 0, {"pp": 10.8}, 0))
    pp = next(c for c in r.submin_checks if c.group == "pp")
    assert pp.required == pytest.approx(0.4 * 27) and pp.passed


def test_ot2_order_d3_on_fallback():
    p = pts(25, 8, 19, 7, {"pp": 27, "sd": 10, "ed": 5, "bonus": 1}, 5)
    r = run("defence", 100_000_000, points=p, tier=YesTier.TARGET_2X)
    assert (r.level_before_discount, r.discounted, r.yes_applied, r.level) == (2, True, True, 1)


def test_tr1_transport_legacy_flag():
    r = run("transport", 100_000_000)
    assert get_sector("transport").status == "legacy"
    assert any("Legacy 2007-Codes" in w for w in r.warnings)


def test_sector_points_only():
    with pytest.raises(ValueError, match="indicator inputs"):
        calculate(ScoreInput(CompanyProfile(100_000_000, sector="tourism"),
                             indicators={"sed": {"x": 1}}))


def test_generic_unchanged_has_no_warnings():
    r = run("generic", 100_000_000, points=pts(22, 5, 14, 15, {"pp": 20, "sd": 8, "ed": 4}, 5))
    assert r.warnings == [] and r.level == 4
