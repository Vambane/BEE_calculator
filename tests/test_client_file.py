"""Client files: save the calculation as JSON, reopen it, reject anything unsafe."""

import json
from datetime import UTC, date, datetime

import pytest

from bee_ui import client_file as cf
from bee_ui.core import fresh_store

WHEN = datetime(2026, 11, 2, 10, 0, tzinfo=UTC)


def filled_store():
    s = fresh_store()
    s["consent"] = True
    s["profile"].update(company="Acme (Pty) Ltd", revenue=120e6, variant=None, yes_prev_level=4)
    s["fin"].update(npat=8e6, tmps=60e6, leviable_amount=30e6, employees=150.0, npat_avg_5y=7e6)
    s["values"]["pct"]["ownership"] = {"100 2.2.1": 30.0, "100 2.3.1": 80.0}
    s["values"]["rand"]["skills"] = {"300 2.1.1": 450_000.0, "300 2.1.9": True}
    s["modes"] = {"skills": "rand"}
    s["entry"] = {"ownership": "ind"}
    s["points"] = {"sed": {"main": 5.0}}
    s["procurement"] = {
        "records": [{"Supplier": "Old", "Spend (R)": 1.0}],
        "current": [{"Supplier": "Acme", "Spend (R)": 1e6, "Empowering supplier": True}],
        "version": 3,
    }
    s["contributions"] = {
        "esd": {"records": [], "version": 2, "current": [{"Amount (R)": float("nan")}]}
    }
    s["net_value"] = {
        "ownership": {
            "entity_value": 1e6,
            "economic_interest_pct": None,
            "equity_date": date(2023, 1, 1),
            "measurement_date": date(2025, 6, 30),
        }
    }
    return s


def roundtrip(s=None, sector="construction", draft=True):
    return cf.parse(cf.dump(s or filled_store(), sector, draft, WHEN))


def test_roundtrip_restores_everything():
    store, app, notes = roundtrip()
    assert notes == []
    assert app == {"sector": "construction", "draft": True, "saved_at": "2026-11-02T10:00:00+00:00"}
    assert store["profile"]["company"] == "Acme (Pty) Ltd"
    assert store["profile"]["yes_prev_level"] == 4 and isinstance(
        store["profile"]["yes_prev_level"], int
    )
    assert store["fin"]["npat_avg_5y"] == 7e6
    assert store["values"]["pct"]["ownership"]["100 2.3.1"] == 80.0
    assert store["values"]["rand"]["skills"]["300 2.1.9"] is True
    assert store["modes"] == {"skills": "rand"} and store["entry"] == {"ownership": "ind"}
    assert store["points"] == {"sed": {"main": 5.0}}
    nv = store["net_value"]["ownership"]
    assert nv["equity_date"] == date(2023, 1, 1) and nv["economic_interest_pct"] is None


def test_live_editor_rows_are_saved_and_editors_reset():
    store, _, _ = roundtrip()
    assert store["procurement"] == {
        "records": [{"Supplier": "Acme", "Spend (R)": 1e6, "Empowering supplier": True}],
        "version": 0,
    }
    box = store["contributions"]["esd"]
    assert box == {"records": [{"Amount (R)": None}], "version": 0, "current": None}  # NaN -> None


def test_consent_is_never_saved_or_restored():
    raw = cf.dump(filled_store(), "generic", False, WHEN)
    assert b"consent" not in raw
    doc = json.loads(raw)
    doc["store"]["consent"] = True
    store, _, _ = cf.parse(json.dumps(doc).encode())
    assert store["consent"] is False


def test_unknown_keys_dropped_and_missing_keys_default():
    doc = json.loads(cf.dump(fresh_store(), "generic", False, WHEN))
    doc["store"]["profile"]["evil"] = "x"
    doc["store"]["surprise"] = {"a": 1}
    del doc["store"]["fin"]
    store, _, _ = cf.parse(json.dumps(doc).encode())
    assert "evil" not in store["profile"] and "surprise" not in store
    assert store["fin"] == fresh_store()["fin"]


def test_wrong_types_reset_with_a_note():
    doc = json.loads(cf.dump(filled_store(), "generic", False, WHEN))
    doc["store"]["fin"]["npat"] = "lots"
    doc["store"]["values"]["pct"]["ownership"]["100 2.2.1"] = {"x": 1}
    store, _, notes = cf.parse(json.dumps(doc).encode())
    assert store["fin"]["npat"] == 0.0
    assert "100 2.2.1" not in store["values"]["pct"]["ownership"]
    assert any("fin.npat" in n for n in notes) and any("ownership" in n for n in notes)


def test_bom_and_utf8_company_names():
    s = fresh_store()
    s["profile"]["company"] = "Ṽenda Ŝolar — Ltd"
    store, _, _ = cf.parse(b"\xef\xbb\xbf" + cf.dump(s, "generic", False, WHEN))
    assert store["profile"]["company"] == "Ṽenda Ŝolar — Ltd"


@pytest.mark.parametrize(
    ("raw", "msg"),
    [
        (b"not json", "not valid JSON"),
        (b"[]", "not a Klim client file"),
        (b'{"format": "other"}', "not a Klim client file"),
        (b'{"format": "bee-check-client"}', "no valid format version"),
        (b'{"format": "bee-check-client", "version": 99, "store": {}}', "newer version"),
        (b'{"format": "bee-check-client", "version": 1}', "no calculation"),
        (b"x" * (cf.MAX_BYTES + 1), "larger than"),
    ],
)
def test_rejects_non_client_files(raw, msg):
    with pytest.raises(cf.ClientFileError, match=msg):
        cf.parse(raw)


def test_row_limit():
    doc = json.loads(cf.dump(fresh_store(), "generic", False, WHEN))
    doc["store"]["procurement"] = {"records": [{"Spend (R)": 1}] * (cf.MAX_ROWS + 5)}
    store, _, notes = cf.parse(json.dumps(doc).encode())
    assert len(store["procurement"]["records"]) == cf.MAX_ROWS
    assert any("rows" in n for n in notes)


def test_row_values_must_be_scalars():
    doc = json.loads(cf.dump(fresh_store(), "generic", False, WHEN))
    doc["store"]["procurement"] = {"records": [{"Supplier": {"$x": 1}, "Spend (R)": 5}, "junk"]}
    store, _, _ = cf.parse(json.dumps(doc).encode())
    assert store["procurement"]["records"] == [{"Supplier": None, "Spend (R)": 5}]


@pytest.mark.parametrize(
    ("company", "name"),
    [
        ("Acme (Pty) Ltd", "klim_acme-pty-ltd_2026-11-02.json"),
        ("", "klim_client_2026-11-02.json"),
        ("../../etc/passwd", "klim_etc-passwd_2026-11-02.json"),
    ],
)
def test_filename_is_safe(company, name):
    assert cf.filename(company, date(2026, 11, 2)) == name


# ------------------------------------------------------------------ security audit fixes
def _doc(store: dict) -> bytes:
    return json.dumps({"format": cf.FORMAT, "version": cf.VERSION, "store": store}).encode()


def test_pdf_gate_and_counters_are_never_saved():
    s = filled_store()
    s["pdf_gate"] = {"email": "a@b.co", "marketing": True, "unlocked": True}
    s["pdf_rate"] = {"unlock_attempts": 1, "pdf_builds": 1}
    s["calc_rate"] = {"calls": 3}
    s["pdf_cache"] = {"key": "k", "bytes": b"%PDF"}
    raw = cf.dump(s, "generic", False, WHEN)
    for token in (b"a@b.co", b"pdf_gate", b"pdf_rate", b"calc_rate", b"pdf_cache", b"consent"):
        assert token not in raw
    store, _, _ = cf.parse(raw)
    assert store["profile"]["company"] == "Acme (Pty) Ltd"
    assert store["procurement"]["records"][0]["Supplier"] == "Acme"


def test_export_holds_only_calculation_sections():
    s = filled_store()
    s["anything_new"] = {"secret": 1}
    doc = json.loads(cf.dump(s, "generic", False, WHEN))
    assert set(doc["store"]) <= set(cf._EXPORT_SECTIONS)


@pytest.mark.parametrize(
    "raw",
    [
        b'{"format": "bee-check-client", "version": 1, "store": '
        + b"[" * 100_000
        + b"]" * 100_000
        + b"}",
        b'{"format": "bee-check-client", "version": ' + b"9" * 5000 + b', "store": {}}',
    ],
    ids=["deep-nesting", "huge-integer"],
)
def test_parser_limits_become_client_file_errors(raw):
    with pytest.raises(cf.ClientFileError):
        cf.parse(raw)


def test_out_of_range_values_are_reset():
    store, _, notes = cf.parse(
        _doc(
            {
                "profile": {"yes_tier": "bogus", "yes_prev_level": 9},
                "modes": {"esd": "nope", "skills": "rand"},
                "entry": {"esd": "weird", "ownership": "pts"},
                "options": {"fs_skills_submin": 7, "fs_rescale_109": "yes", "start_up": True},
            }
        )
    )
    assert store["profile"]["yes_tier"] == "none"
    assert store["profile"]["yes_prev_level"] is None
    assert store["modes"] == {"skills": "rand"}
    assert store["entry"] == {"ownership": "pts"}
    assert store["options"] == {"start_up": True}
    assert any("yes_tier" in n for n in notes)


def test_valid_previous_level_kept_as_int():
    store, _, _ = cf.parse(_doc({"profile": {"yes_prev_level": 3.0}}))
    assert store["profile"]["yes_prev_level"] == 3


def test_unknown_and_excess_element_keys_are_dropped():
    bad = "**EL** [x](https://example.invalid)"
    store, _, notes = cf.parse(
        _doc(
            {
                "values": {"pct": {bad: {"c": 1.0}, "ownership": {"c": 1.0}}},
                "net_value": {f"el{i}": {"entity_value": 1.0} for i in range(cf.MAX_ELEMENTS + 10)},
            }
        )
    )
    assert list(store["values"]["pct"]) == ["ownership"]
    assert len(store["net_value"]) == cf.MAX_ELEMENTS
    assert not any(bad in n or "https://" in n for n in notes)


def test_company_name_capped_like_the_profile_input():
    store, _, _ = cf.parse(_doc({"profile": {"company": "A" * 400}}))
    assert len(store["profile"]["company"]) == 120
