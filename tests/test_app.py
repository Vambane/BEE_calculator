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


def sync_profile_keys(at):
    """Keep bind()+key widgets aligned after programmatic store writes (step 0)."""
    p = at.session_state["store"]["profile"]
    f = at.session_state["store"]["fin"]
    at.session_state["profile_revenue"] = float(p.get("revenue") or 0.0)
    at.session_state["profile_black_ownership"] = float(p.get("black_ownership") or 0.0)
    at.session_state["fin_npat"] = float(f.get("npat") or 0.0)
    at.session_state["fin_leviable_amount"] = float(f.get("leviable_amount") or 0.0)
    at.session_state["fin_tmps"] = float(f.get("tmps") or 0.0)
    at.session_state["fin_employees"] = float(f.get("employees") or 0.0)


def sidebar_labels(at):
    """Sidebar step labels may be markdown (current/locked) or buttons (reachable)."""
    labels = [m.value or "" for m in at.sidebar.markdown]
    labels += [b.label or "" for b in at.sidebar.button]
    return labels


def click_continue(at):
    """Click the primary Continue footer button (not sidebar Start over / nav)."""
    btn = next(b for b in at.button if (b.label or "").startswith("Continue"))
    return btn.click().run()


def test_profile_renders_with_privacy_and_generic_default():
    at = boot()
    assert not at.exception
    assert any("Privacy notice" in m.value for m in at.markdown)
    assert any("s26" in (m.value or "") for m in at.markdown)
    assert any("app host" in (m.value or "") for m in at.markdown)
    assert any("Full privacy notice" in (e.label or "") for e in at.expander)
    assert any("agree to this processing for this session" in (c.label or "") for c in at.checkbox)
    assert at.selectbox[0].value == "generic"


def test_continue_blocked_without_consent():
    at = boot()
    click_continue(at)
    assert any("consent" in e.value for e in at.error)
    assert at.session_state["step"] == 0


def test_consent_error_clears_after_tick():
    """UX-M1: stale 'Tick the privacy consent box' must clear once consent is ticked."""
    at = boot()
    click_continue(at)
    assert any("consent" in (e.value or "").lower() for e in at.error)
    for c in at.checkbox:
        if "privacy" in (c.label or "").lower() or "agree" in (c.label or "").lower():
            c.check()
            break
    else:
        raise AssertionError("privacy consent checkbox not found")
    at.run()
    assert at.session_state["store"]["consent"] is True
    assert not any("consent" in (e.value or "").lower() for e in at.error)
    assert "_step_errs_0" not in at.session_state or not at.session_state.get("_step_errs_0")


def test_step_query_without_consent_stays_on_profile():
    """H1: ?step= must not skip the POPIA consent gate."""
    at = boot(step="2")
    assert not at.exception
    assert at.session_state["step"] == 0
    assert any("Privacy notice" in m.value for m in at.markdown)
    assert any("privacy notice" in (c.label or "").lower() for c in at.checkbox)
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
    steps = sidebar_labels(at)
    assert not any("Enterprise Development" in s for s in steps)
    at = boot(sector="financial")
    at.session_state["store"]["profile"]["variant"] = "bank"
    at = to_results(at)
    assert any("Access to Financial Services" in s for s in sidebar_labels(at))


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


def test_privacy_page_query_renders_policy():
    """?page=privacy shows the policy from docs/PRIVACY.md (in-app /privacy stand-in)."""
    at = boot(page="privacy")
    assert not at.exception
    assert any("Privacy policy" in (t.value or "") for t in at.title)
    body = " ".join(m.value or "" for m in at.markdown)
    assert "Streamlit Community Cloud" in body
    assert "s72" in body
    assert "[Legal entity name" in body or "Legal entity name" in body
    assert any("Back to calculator" in (b.label or "") for b in at.button)
    assert "How to use" in body


def test_howto_page_query_renders_guide():
    """?page=howto shows docs/HOW_TO.md (in-app /howto stand-in); no wizard chrome needed."""
    at = boot(page="howto")
    assert not at.exception
    assert any("How to use" in (t.value or "") for t in at.title)
    body = " ".join(m.value or "" for m in at.markdown)
    assert "planning estimate" in body.lower() or "Planning estimate" in body
    assert "Start over" in body
    assert "Privacy policy" in body or "?page=privacy" in body
    assert any("Back to calculator" in (b.label or "") for b in at.button)


def test_profile_shows_howto_oneliner():
    """Profile always shows New here? How to use this calculator link."""
    at = boot()
    assert not at.exception
    body = " ".join(m.value or "" for m in at.markdown)
    assert "How to use this calculator" in body
    assert "?page=howto" in body
    side = " ".join(m.value or "" for m in at.sidebar.markdown)
    assert "How to use" in side
    assert "?page=howto" in side
    assert "Privacy policy" in side


def test_pdf_gate_marketing_is_honest_not_a_list():
    """Compliance §2 / Security M6: marketing tick must not claim a mailing-list subscribe."""
    at = to_results(boot())
    assert not at.exception
    labels = " ".join((c.label or "") for c in at.checkbox)
    caps = " ".join((c.value or "") for c in at.caption)
    md = " ".join((m.value or "") for m in at.markdown)
    helps = " ".join((c.help or "") for c in at.checkbox)
    blob = labels + " " + caps + " " + md + " " + helps
    low = blob.lower()
    assert "does not add you to a mailing list" in low or "mailing list in v1" in low
    assert "we do not email the report" in low or "do not email the report" in low
    assert any("Continue with email" in (b.label or "") for b in at.button)
    # UX-M5: no developer stubs on the PDF gate
    assert "deferred" not in low
    assert "cloud-edge" not in low
    assert "marketing email provider" not in low
    assert "no marketing email" not in low


def test_empty_results_no_level9_discount_punishment():
    """UX-M7: 0 points entered must not say 'discounted from Level 9'."""
    at = to_results(boot())
    assert not at.exception
    warnings = " ".join((w.value or "") for w in at.warning)
    infos = " ".join((i.value or "") for i in at.info)
    assert "discounted from Level 9" not in warnings
    assert "Sub-minimum missed" not in warnings or "Level 9" not in warnings
    assert "No points entered" in infos or "enter indicators or points" in infos.lower()


def test_unexpected_calculate_shows_support_caption(monkeypatch):
    """Unexpected engine failures: generic error + time-only support caption (no PII)."""
    import bee

    def boom(*_a, **_k):
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr(bee, "calculate", boom)
    at = to_results(boot())
    assert not at.exception
    assert any("could not calculate" in (e.value or "").lower() for e in at.error)
    caps = " ".join(c.value or "" for c in at.caption)
    assert "score calculation" in caps
    assert "contact support" in caps.lower()
    assert "synthetic failure" not in caps
    assert "qa@" not in caps.lower()


# --- full-scorecard v1.1 gender visibility (Compliance acceptance) ---


def test_ownership_defaults_to_indicators_and_shows_women_clauses():
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    at.session_state["step"] = 1  # Ownership
    at.run()
    assert not at.exception
    assert at.session_state["store"]["entry"].get("ownership", "ind") == "ind"
    labels = " ".join(n.label or "" for n in at.number_input)
    # Paired short labels or full names — clause help still carries targets.
    helps = " ".join((n.help or "") for n in at.number_input)
    assert "100 2.1.2" in helps
    assert "100 2.2.2" in helps
    assert "Black women" in labels or "black women" in labels.lower()


def test_management_shows_six_black_female_lines_by_default():
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    # Find management step index dynamically
    at.session_state["step"] = 2
    at.run()
    assert not at.exception
    # Ensure we're on Management (step order: Profile, Ownership, Management, ...)
    assert at.session_state["store"]["entry"].get("management", "ind") == "ind"
    helps = " ".join((n.help or "") for n in at.number_input)
    for cl in (
        "200 2.1.2",
        "200 2.1.4",
        "200 2.2.2",
        "200 2.3.2",
        "200 2.4.2",
        "200 2.5.2",
    ):
        assert cl in helps, cl


def test_qse_ownership_women_visible_by_default():
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 20_000_000.0  # QSE
    at.session_state["step"] = 1
    at.run()
    assert not at.exception
    helps = " ".join((n.help or "") for n in at.number_input)
    assert "601 2.1.1.2" in helps
    assert "601 2.1.2.2" in helps


def test_results_gender_contribution_positive_when_women_entered():
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 100_000_000.0
    store["fin"].update(
        npat=10_000_000.0, tmps=50_000_000.0, leviable_amount=20_000_000.0, employees=100.0
    )
    store["entry"]["ownership"] = "ind"
    store["entry"]["management"] = "ind"
    store["modes"]["ownership"] = "pct"
    store["modes"]["management"] = "pct"
    store["values"]["pct"]["ownership"] = {
        "100 2.1.1": 25.0,
        "100 2.1.2": 10.0,
        "100 2.2.1": 25.0,
        "100 2.2.2": 10.0,
        "100 2.3.1": 50.0,
    }
    store["values"]["pct"]["management"] = {"200 2.1.2": 25.0}
    at.session_state["step"] = 99
    at.run()
    assert not at.exception, at.exception
    metric_text = " ".join(f"{m.label or ''} {m.value or ''}" for m in at.metric)
    assert "Black women / Black female contribution" in metric_text
    assert "of" in metric_text
    # X > 0
    assert any(
        m.label == "Black women / Black female contribution"
        and m.value
        and not str(m.value).startswith("0")
        for m in at.metric
    )


def test_profile_has_no_women_ownership_field():
    at = boot()
    labels = [n.label or "" for n in at.number_input]
    assert any("Black ownership" in lab for lab in labels)
    assert not any("women ownership" in lab.lower() for lab in labels)


def test_demo_does_not_force_points_on_ownership():
    at = boot(demo="1")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    at.run()
    assert at.session_state["store"]["entry"].get("ownership") == "ind"
    assert at.session_state["store"]["entry"].get("management") == "ind"


def test_honey_theme_css_via_html_not_markdown():
    """UX-C1: theme CSS + hex must go through st.html so tags are not visible markdown."""
    at = boot()
    assert not at.exception
    md = "\n".join(m.value or "" for m in at.markdown)
    assert "<style>" not in md
    assert "bee-hex-divider" not in md
    html = "\n".join(h.value or "" for h in at.html)
    assert ".bee-hex-divider" in html or "Honey visual" in html
    assert "Material Symbols Rounded" in html  # UX-C3 icon-font restore lives in same block
    at = to_results(boot())
    assert not at.exception
    html = "\n".join(h.value or "" for h in at.html)
    assert 'class="bee-hex-divider"' in html or "bee-hex-divider" in html
    md = "\n".join(m.value or "" for m in at.markdown)
    assert '<div class="bee-hex-divider"' not in md


def test_eme_opt_scored_shows_ownership_and_mc_steps():
    """UX-C2: EME + full-scorecard opt-in must expose QSE element steps."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 5_000_000.0
    store["profile"]["black_ownership"] = 51.0
    store["profile"]["opt_scored"] = True
    sync_profile_keys(at)
    at.run()
    assert not at.exception
    side = " ".join(sidebar_labels(at))
    assert "Ownership" in side
    assert "Management Control" in side or "Management" in side
    assert "Skills Development" in side or "Skills" in side
    at.session_state["step"] = 1
    at.run()
    assert not at.exception
    assert any((t.value or "") == "Ownership" for t in at.title)


def test_eme_deemed_sidebar_is_profile_and_results_only():
    """EME without opt_scored stays affidavit-only (no Ownership/MC steps)."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 5_000_000.0
    store["profile"]["black_ownership"] = 60.0
    store["profile"]["opt_scored"] = False
    sync_profile_keys(at)
    at.run()
    assert not at.exception
    side = " ".join(sidebar_labels(at))
    assert "Ownership" not in side
    assert "Management" not in side
    assert "Results" in side


def test_eme_deemed_hides_gender_contribution_metric():
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 5_000_000.0  # EME
    store["profile"]["black_ownership"] = 60.0
    store["profile"]["opt_scored"] = False
    at.session_state["step"] = 99
    at.run()
    assert not at.exception
    assert not any(m.label == "Black women / Black female contribution" for m in at.metric)


def test_tourism_ownership_women_help_shows_15():
    at = boot(sector="tourism")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 50_000_000.0  # Large
    at.session_state["step"] = 1
    at.run()
    assert not at.exception
    helps = " ".join((n.help or "") for n in at.number_input)
    assert "Target 15" in helps


def test_bo_over_100_blocks_continue():
    """F-EDGE-OVER100: BO 101% must block Continue (not score as empty/L4)."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 5_000_000.0  # EME deemed path
    store["profile"]["black_ownership"] = 101.0
    sync_profile_keys(at)
    at.run()
    assert at.session_state["step"] == 0
    # Primary Continue is the last button on the profile footer
    click_continue(at)
    assert at.session_state["step"] == 0
    assert any("Black ownership must be between 0% and 100%" in (e.value or "") for e in at.error)


def test_bo_over_100_stale_prior_does_not_advance():
    """F-EDGE-OVER100: after a valid 51%, typing 101 must not keep prior L2 via Continue."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 5_000_000.0
    store["profile"]["black_ownership"] = 51.0
    sync_profile_keys(at)
    at.run()
    # Simulate editing BO to 101 while still on Profile (stale session risk)
    at.session_state["store"]["profile"]["black_ownership"] = 101.0
    sync_profile_keys(at)
    at.run()
    click_continue(at)
    assert at.session_state["step"] == 0
    assert any("Black ownership must be between 0% and 100%" in (e.value or "") for e in at.error)


def test_bo_over_100_results_does_not_score():
    """Results with BO 101 must show validation error and no Recognition level."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 5_000_000.0
    store["profile"]["black_ownership"] = 101.0
    at.session_state["step"] = 99
    at.run()
    assert not at.exception
    assert any("Black ownership must be between 0% and 100%" in (e.value or "") for e in at.error)
    assert not any(m.label == "Recognition level" for m in at.metric)


def test_negative_revenue_blocks_continue():
    """Security M3 / Batch1: revenue -1 must block Continue on the same gate."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = -1.0
    store["profile"]["black_ownership"] = 30.0
    sync_profile_keys(at)
    at.run()
    click_continue(at)
    assert at.session_state["step"] == 0
    assert any("revenue" in (e.value or "").lower() for e in at.error)


def test_revenue_number_input_commits_and_size_same_run():
    """MBC-BUG-01: after setting revenue, store + Size badge match (no flap / lag)."""
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 5_000_000.0
    at.session_state["profile_revenue"] = 5_000_000.0
    at.run()
    assert not at.exception
    rev = next(n for n in at.number_input if "Total revenue" in (n.label or ""))
    rev.set_value(10_000_000.0).run()
    assert not at.exception
    assert at.session_state["store"]["profile"]["revenue"] == 10_000_000.0
    assert at.session_state.get("profile_revenue") == 10_000_000.0
    caps = " ".join((c.value or "") for c in at.caption)
    # Generic size_labels: EME → "EME" / Exempt Micro Enterprise style
    assert "EME" in caps or "Exempt" in caps
    # Cross EME→QSE boundary in one set_value; after optional size-rerun, badge is QSE.
    rev = next(n for n in at.number_input if "Total revenue" in (n.label or ""))
    rev.set_value(10_000_001.0).run()
    assert at.session_state["store"]["profile"]["revenue"] == 10_000_001.0
    caps = " ".join((c.value or "") for c in at.caption)
    assert "QSE" in caps


def test_pdf_invalid_email_shows_error_and_does_not_unlock():
    """MBC-F02: not-an-email must show a clear error and must not unlock the PDF."""
    at = to_results(boot())
    assert not at.exception
    assert any("Continue with email" in (b.label or "") for b in at.button)
    email = next(t for t in at.text_input if "email" in (t.label or "").lower())
    email.set_value("not-an-email").run()
    btn = next(b for b in at.button if "Continue with email" in (b.label or ""))
    btn.click().run()
    assert not at.exception
    gate = at.session_state["store"].get("pdf_gate") or {}
    assert not gate.get("unlocked")
    assert any("valid email" in (e.value or "").lower() for e in at.error)
    # @@ also rejected
    email = next(t for t in at.text_input if "email" in (t.label or "").lower())
    email.set_value("@@").run()
    btn = next(b for b in at.button if "Continue with email" in (b.label or ""))
    btn.click().run()
    assert not at.session_state["store"]["pdf_gate"].get("unlocked")
    assert any("valid email" in (e.value or "").lower() for e in at.error)


def test_sidebar_step_button_navigates_without_clearing_inputs():
    """UX polish: clicking a reached sidebar step jumps there; inputs preserved."""
    at = boot()
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"]["revenue"] = 100_000_000.0
    store["profile"]["black_ownership"] = 40.0
    store["values"]["pct"]["ownership"] = {"2.1.1": 25.0}
    sync_profile_keys(at)
    at.session_state["step"] = 2
    at.session_state["max_step"] = 2
    at.run()
    assert not at.exception
    assert at.session_state["step"] == 2
    btn = next(b for b in at.sidebar.button if "Ownership" in (b.label or ""))
    btn.click().run()
    assert at.session_state["step"] == 1
    assert at.session_state["store"]["profile"]["black_ownership"] == 40.0
    assert at.session_state["store"]["values"]["pct"]["ownership"]["2.1.1"] == 25.0


def test_sidebar_cannot_jump_past_max_reached_or_without_consent():
    """Cold start / no consent: unreached steps are not clickable nav buttons."""
    at = boot()
    assert at.session_state["step"] == 0
    assert not any(
        (b.label or "").endswith("Ownership") or "Ownership" in (b.label or "")
        for b in at.sidebar.button
        if (b.label or "") != "Start over"
    )
    # Consent + stay on profile: Ownership still locked (max_step 0).
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    sync_profile_keys(at)
    at.session_state["step"] = 0
    at.session_state["max_step"] = 0
    at.run()
    # Unreached steps stay markdown (○), not nav buttons.
    assert not any("Ownership" in (b.label or "") for b in at.sidebar.button)
    assert any("Ownership" in (m.value or "") for m in at.sidebar.markdown)


def test_start_over_clears_scenario_and_returns_to_profile():
    """Start over clears ownership/indicators/points/PDF unlock; keeps draft pref."""
    at = boot(draft="1")
    store = at.session_state["store"]
    store["consent"] = True
    store["profile"].update(
        company="Bleed Co", revenue=100_000_000.0, black_ownership=55.0, opt_scored=True
    )
    store["fin"]["npat"] = 9_000_000.0
    store["values"]["pct"]["ownership"] = {"2.1.1": 40.0}
    store["points"]["skills"] = {"main": 10.0}
    store["entry"]["ownership"] = "ind"
    store["pdf_gate"] = {"email": "a@b.co", "marketing": True, "unlocked": True}
    store["pdf_cache"] = {"key": "x", "bytes": b"%PDF"}
    at.session_state["profile_black_ownership"] = 55.0
    at.session_state["step"] = 3
    at.session_state["max_step"] = 3
    at.run()
    assert at.session_state["draft"] is True
    btn = next(b for b in at.sidebar.button if (b.label or "") == "Start over")
    btn.click().run()
    assert not at.exception
    assert at.session_state["step"] == 0
    assert at.session_state["max_step"] == 0
    s = at.session_state["store"]
    assert s["consent"] is False
    assert s["profile"]["company"] == ""
    assert s["profile"]["black_ownership"] == 0.0
    assert s["profile"]["revenue"] == 0.0
    assert s["values"] == {"rand": {}, "pct": {}}
    assert s["points"] == {}
    assert s["entry"] == {}
    assert "pdf_gate" not in s
    assert "pdf_cache" not in s
    # bind() re-seeds profile_* from the fresh store (0.0), not the prior 55%.
    assert at.session_state.get("profile_black_ownership") == 0.0
    assert at.session_state["draft"] is True  # ruleset pref kept


# ------------------------------------------------------------------ procurement calculator
def _esd_step(records=None, mode="pct"):
    at = boot()
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0
    at.session_state["store"]["modes"]["esd"] = mode
    if records is not None:
        at.session_state["store"]["procurement"] = {"records": records, "version": 0}
    at.session_state["step"] = 4  # Generic: Ownership, MC, Skills, ESD
    return at.run()


_REC = {
    "Supplier": "Acme",
    "Spend (R)": 1_000_000.0,
    "B-BBEE level": "1",
    "Size": "QSE",
    "Black ownership %": 100.0,
    "Black women ownership %": 60.0,
    "Designated group": False,
    "Empowering supplier": True,
    "TMPS exclusion": "Included in TMPS",
}
_TAX = _REC | {
    "Supplier": "SARS",
    "Spend (R)": 250_000.0,
    "B-BBEE level": "NC",
    "Size": "Unknown",
    "Black ownership %": 0.0,
    "Black women ownership %": 0.0,
    "TMPS exclusion": "Taxes, levies and duties",
}


def test_esd_step_offers_supplier_list_calculator():
    at = _esd_step()
    assert not at.exception
    assert any("supplier list" in (e.label or "") for e in at.expander)


@pytest.mark.parametrize("mode", ["pct", "rand"])
def test_supplier_list_sets_tmps_and_fills_indicators(mode):
    at = _esd_step([_REC, _TAX], mode)
    assert not at.exception
    tmps = next(m for m in at.metric if m.label == "TMPS")
    assert tmps.value == "R1 000 000"
    next(b for b in at.button if b.label == "Use these figures").click().run()
    assert not at.exception
    store = at.session_state["store"]
    assert store["fin"]["tmps"] == 1_000_000.0
    esd = store["values"][mode]["esd"]
    # Level 1 supplier: recognised 135% of TMPS on the all-suppliers measure.
    expected = 135.0 if mode == "pct" else 1_350_000.0
    assert esd["400 2.1.1"] == pytest.approx(expected)
    assert any("Applied" in s.value for s in at.success)


def test_supplier_list_not_shown_on_points_entry_or_cards_without_pp_table():
    at = boot(sector="ict")
    at.session_state["store"]["consent"] = True
    at.session_state["store"]["profile"]["revenue"] = 100_000_000.0  # ICT Large: points only
    at.session_state["step"] = 4
    at.run()
    assert not at.exception
    assert not any("supplier list" in (e.label or "") for e in at.expander)


def test_start_over_clears_supplier_list():
    from bee_ui.core import fresh_store, is_scenario_widget_key

    assert fresh_store()["procurement"] == {"records": [], "version": 0}
    assert is_scenario_widget_key("proc_editor_3")
