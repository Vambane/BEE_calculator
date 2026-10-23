"""AppTest smoke runs of the Streamlit UI (engine does the scoring)."""

from pathlib import Path

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = st_testing.AppTest
APP = Path(__file__).resolve().parent.parent / "app.py"


def boot(**qp):
    at = AppTest.from_file(str(APP), default_timeout=30)
    for k, v in qp.items():
        at.query_params[k] = v
    return at.run()


def to_results(at):
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    at.session_state["store"]["fin"].update(
        npat=10_000_000.0, tmps=50_000_000.0, leviable_amount=20_000_000.0, employees=100.0
    )
    at.session_state["step"] = 99
    return at.run()


def test_profile_renders_with_privacy_and_generic_default():
    at = boot()
    assert not at.exception
    assert any("Privacy notice" in m.value for m in at.markdown)
    assert any("s26" in (m.value or "") for m in at.markdown)
    assert at.selectbox[0].value == "generic"


def test_continue_blocked_without_consent():
    at = boot()
    at.button[-1].click().run()
    assert any("consent" in e.value for e in at.error)
    assert at.session_state["step"] == 0


def test_step_query_without_consent_stays_on_profile():
    """H1: ?step= must not skip the POPIA consent gate."""
    at = boot(step="2")
    assert not at.exception
    assert at.session_state["step"] == 0
    assert any("Privacy notice" in m.value for m in at.markdown)
    assert any("consent" in (c.label or "").lower() for c in at.checkbox)
    at = boot(step="99")
    assert at.session_state["step"] == 0
    assert any("Privacy notice" in m.value for m in at.markdown)


def test_demo_does_not_auto_consent():
    """M3: ?demo=1 seeds figures but must not tick consent for the user."""
    at = boot(demo="1")
    assert not at.exception
    assert at.session_state["store"]["consent"] is False
    assert at.session_state["step"] == 0


@pytest.mark.parametrize(
    "sector", ["generic", "construction", "financial", "agri", "tourism", "ict", "mac"]
)
def test_results_render_for_each_sector(sector):
    at = boot(sector=sector)
    at = to_results(at)
    assert not at.exception
    assert any(m.label == "Recognition level" for m in at.metric)
    assert any(e.label == "Interpretation notes" for e in at.expander)


def test_badges():
    at = to_results(boot(sector="construction"))
    assert any("Verified sector code" in m.value for m in at.markdown)
    at = to_results(boot(sector="ict"))
    assert any("Verified sector code" in m.value for m in at.markdown)
    assert not any("Pending expert" in m.value for m in at.markdown)
    at = to_results(boot(sector="mac"))
    assert any("fallback" in w.value for w in at.warning)


def test_results_show_out_of_max():
    at = boot(sector="tourism")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 20_000_000.0  # QSE → out of 101
    at.session_state["step"] = 99
    at.run()
    assert any(m.value and "out of 101" in m.value for m in at.metric)
    at = boot(sector="construction")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 20_000_000.0
    at.session_state["store"]["profile"]["variant"] = "contractor"
    at.session_state["step"] = 99
    at.run()
    text = " ".join(filter(None, (m.value for m in list(at.metric) + list(at.caption))))
    assert "out of 110" in text


def test_construction_has_no_ed_and_fs_bank_has_afs_step():
    at = to_results(boot(sector="construction"))
    steps = [m.value for m in at.sidebar.markdown]
    assert not any("Enterprise Development" in s for s in steps)
    at = boot(sector="financial")
    at.session_state["store"]["profile"]["variant"] = "bank"
    at = to_results(at)
    assert any("Access to Financial Services" in m.value for m in at.sidebar.markdown)


def test_r50m_generic_card_via_engine():
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 50_000_000.0
    at.session_state["step"] = 99
    at.run()
    assert any("Generic" in m.value for m in at.markdown if m.value.startswith("**Scorecard"))


def test_draft_off_hides_tf_tab_and_on_shows_it():
    at = to_results(boot())
    assert not any("TF vs" in t.label for t in at.tabs)
    at = to_results(boot(draft="1"))
    assert any("TF vs" in t.label for t in at.tabs)


def test_net_value_input_on_ownership_step():
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    at.session_state["step"] = 1
    at.run()
    assert any("Net Value points (0 to 8)" in n.label for n in at.number_input)


def test_points_over_cap_rejected_not_clamped():
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    at.session_state["store"]["entry"]["skills"] = "pts"
    at.session_state["store"]["points"]["skills"] = {"main": 999.0}  # max 20
    at.session_state["step"] = 99
    at.run()
    assert any("max 20" in e.value for e in at.error)


def test_ict_qse_uses_sector_card():
    at = boot(sector="ict")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 20_000_000.0
    at.session_state["step"] = 99
    at.run()
    assert not at.exception
    assert any(
        "ict-qse" in str(m.value).lower()
        or "ICT QSE" in m.value
        or "AICT" in m.value
        or "Pending expert" in m.value
        for m in list(at.markdown) + list(at.warning)
    )


def test_pdf_email_gate_then_download():
    at = to_results(boot())
    assert not at.exception
    assert any("Continue with email" in (b.label or "") for b in at.button)
    at.session_state["store"]["pdf_gate"] = {
        "email": "qa@example.com",
        "marketing": False,
        "unlocked": True,
    }
    at.run()
    assert any("PDF" in (b.label or "") for b in at.download_button)


def test_deemed_results_hide_pdf_gate_and_explain():
    """Deemed affidavit path: no PDF/email gate; caption points to full-scorecard option."""
    at = boot(sector="construction")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 20_000_000.0  # QSE
    at.session_state["store"]["profile"]["variant"] = "contractor"
    at.session_state["store"]["profile"]["black_ownership"] = 100.0
    at.session_state["store"]["profile"]["opt_scored"] = False
    at.session_state["step"] = 99
    at.run()
    assert not at.exception, at.exception
    assert not any("Continue with email" in (b.label or "") for b in at.button)
    assert not any("PDF" in (b.label or "") for b in at.download_button)
    caps = " ".join(c.value or "" for c in at.caption)
    infos = " ".join(i.value or "" for i in at.info)
    assert "PDF gap report" in (caps + infos)


def test_draft_toggle_shows_not_in_force_banner():
    at = to_results(boot(draft="1"))
    assert any("NOT IN FORCE" in (w.value or "") for w in at.warning)


def test_b16_empty_scorecard_chart_does_not_crash():
    """EME full-scorecard with no points: Results must not AttributeError on empty chart df."""
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 5_000_000.0
    at.session_state["store"]["profile"]["opt_scored"] = True
    at.session_state["step"] = 99
    at.run()
    assert not at.exception, at.exception


def test_pdf_unlock_rate_limit_blocks_after_max_attempts():
    at = to_results(boot())
    assert not at.exception
    at.session_state["store"]["pdf_rate"] = {"unlock_attempts": 5, "pdf_builds": 0}
    at.run()
    assert not at.exception
    errors = [e.value for e in at.error]
    assert any("Too many unlock attempts" in (e or "") for e in errors)
    assert not any("Continue with email" in (b.label or "") for b in at.button)


def test_pdf_build_rate_limit_blocks_when_exhausted():
    at = to_results(boot())
    at.session_state["store"]["pdf_gate"] = {
        "email": "qa@example.com",
        "marketing": False,
        "unlocked": True,
    }
    at.session_state["store"]["pdf_rate"] = {"unlock_attempts": 1, "pdf_builds": 5}
    # No cache → should hit build limit without calling WeasyPrint.
    at.session_state["store"].pop("pdf_cache", None)
    at.run()
    assert not at.exception
    errors = [e.value for e in at.error]
    assert any("PDF build limit" in (e or "") for e in errors)
    assert not any("PDF" in (b.label or "") for b in at.download_button)
