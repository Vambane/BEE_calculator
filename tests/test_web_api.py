"""The browser build's JSON API (bee_web.api) must mirror the Streamlit app's engine calls."""

import json

import pytest

from bee import calculate
from bee_ui import client_file
from bee_ui.core import build_input
from bee_web import api


def call(name, *args):
    out = json.loads(api.call(name, json.dumps(list(args))))
    assert "error" not in out, out
    return out


@pytest.fixture
def session():
    store = call("fresh")
    store["consent"] = True
    store["profile"].update(company="Acme (Pty) Ltd", revenue=120e6, black_ownership=40.0)
    store["fin"].update(npat=8e6, leviable_amount=30e6, tmps=60e6, employees=150.0)
    store["values"]["pct"]["ownership"] = {"100 2.2.1": 30.0, "100 2.3.1": 80.0}
    store["entry"] = {"ownership": "ind"}
    return {"store": store, "sector": "generic", "draft": False, "default_mode": "rand"}


def test_meta_lists_every_sector_with_generic_first():
    m = call("meta")
    assert m["sectors"][0]["key"] == "generic"
    assert len(m["sectors"]) >= 13
    assert m["client_file"]["format"] == client_file.FORMAT


def test_context_steps_and_element_forms(session):
    c = call("context", session)
    assert [s["key"] for s in c["steps"]][0] == "profile"
    assert c["steps"][-1]["key"] == "results"
    own = c["elements"]["ownership"]
    assert own["mode"] == "pct" and not own["can_rand"]  # Ownership is percentage-only
    assert own["net_value"]["points"] > 0
    assert any(u["kind"] == "pair" for u in own["units"])


def test_score_matches_the_engine_directly(session):
    r = call("score", session)
    st = session["store"]
    values = {k: st["values"][st["modes"].get(k, "pct")].get(k, {}) for k in st["values"]["pct"]}
    direct = calculate(
        build_input(
            "generic",
            None,
            st["profile"],
            api._Session(session).fin(effective=False),
            values,
            st["modes"],
            st["points"],
            False,
            st["options"],
            st["entry"],
        )
    )
    assert r["ok"] and r["level_label"] == direct.level_label
    assert r["total"] == pytest.approx(direct.total_points)


def test_score_refuses_without_consent(session):
    session["store"]["consent"] = False
    r = call("score", session)
    assert not r["ok"] and "consent" in r["problems"][0]


def test_profile_problems_block_bad_ownership(session):
    session["store"]["profile"]["black_ownership"] = 140.0
    assert any("Black ownership" in p for p in call("problems", session, "profile"))


def test_convert_mode_rand_to_pct_through_profile_base(session):
    session["store"]["modes"]["skills"] = "rand"
    session["store"]["values"]["rand"]["skills"] = {"300 2.1.1.1": 450_000.0}
    store = call("convert_mode", session, "skills", "pct")
    assert store["modes"]["skills"] == "pct"
    assert store["values"]["pct"]["skills"]["300 2.1.1.1"] == pytest.approx(1.5)  # of payroll


def test_client_file_round_trip_keeps_consent_out(session):
    saved = call("client_save", session)
    assert "consent" not in json.loads(saved["text"])["store"]
    opened = call("client_open", saved["text"])
    assert opened["ok"] and opened["store"]["profile"]["company"] == "Acme (Pty) Ltd"
    assert opened["store"]["consent"] is False


def test_procurement_summary_from_template(session):
    parsed = call("procurement_parse_csv", call("procurement_template"))
    assert parsed["ok"] and parsed["records"]
    s = call("procurement_summary", session, "esd", parsed["records"])
    assert (
        s["tmps"] > 0
        and s["rows"]
        and s["csv"].startswith('"Supplier"')
        or s["csv"].startswith("Supplier")
    )


def test_net_value_lower_of_formulas(session):
    box = {
        "entity_value": 1e8,
        "black_equity_value": 4e7,
        "acquisition_debt": 1e7,
        "economic_interest_pct": 40,
        "equity_date": "2022-01-01",
        "measurement_date": "2026-06-30",
        "target_pct": 25,
    }
    nv = call("net_value", session, "ownership", box)
    assert nv["ok"] and 0 <= nv["points"] <= nv["max"]


def test_report_context_for_print(session):
    rep = call("report", session)
    assert rep["ok"] and rep["company"]["name"] == "Acme (Pty) Ltd"
    assert rep["result"]["elements"]


def test_unknown_call_is_an_error_not_an_exception():
    assert "error" in json.loads(api.call("nope", "[]"))
