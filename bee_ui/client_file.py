"""Client files: save a whole calculation to a JSON file and open it again later.

The app keeps nothing between sessions, so an accountant with many clients saves one
file per client (and per measurement year) on their own device and reopens it later.

Format (``FORMAT`` / ``VERSION``)::

    {
      "format": "bee-check-client",
      "version": 1,
      "saved_at": "2026-11-02T12:00:00+00:00",
      "app": {"sector": "generic", "draft": false},
      "store": { ...the canonical session store, minus consent... }
    }

Loading is defensive: the file is untrusted input. Only keys the current app knows are
kept, every value is type-checked against a fresh store, and anything missing falls back
to its default, so files from older versions still open. Consent is never read from a
file: the person opening it must agree to the privacy notice themselves.
"""

from __future__ import annotations

import json
import math
import re
from datetime import UTC, date, datetime
from typing import Any

from bee_ui.core import fresh_store

FORMAT = "bee-check-client"
VERSION = 1
MAX_BYTES = 2_000_000  # a 5 000-row supplier list is well under 1 MB
MAX_ROWS = 10_000

# Store sections and how to restore them.
_SCALAR_SECTIONS = ("profile", "fin")  # fixed keys, typed like fresh_store()
_NUMBER_MAPS = ("points",)  # element -> {group: number}
_STRING_MAPS = ("modes", "entry")  # element -> str
_DATE_KEYS = frozenset({"equity_date", "measurement_date"})
_SLUG = re.compile(r"[^A-Za-z0-9]+")


class ClientFileError(ValueError):
    """The file could not be opened; ``problems`` lists every reason found."""

    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("; ".join(problems))


# ------------------------------------------------------------------ save
def _clean(obj: Any) -> Any:
    """JSON-safe copy: dates to ISO strings, NaN/inf to None, tuples to lists."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_clean(v) for v in obj]
    if isinstance(obj, datetime | date):
        return obj.isoformat()
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if obj is None or isinstance(obj, bool | int | float | str):
        return obj
    if hasattr(obj, "item"):  # numpy / pandas scalars from data editors
        return _clean(obj.item())
    return str(obj)


def dump(store: dict, sector: str, draft: bool, saved_at: datetime | None = None) -> bytes:
    """Serialise the calculation. Consent is left out on purpose."""
    body = {k: v for k, v in store.items() if k != "consent"}
    # Save what is on screen: each contributions editor's live rows ("current").
    body["contributions"] = {
        el: {
            "records": box["current"] if box.get("current") is not None else box.get("records", [])
        }
        for el, box in (store.get("contributions") or {}).items()
        if isinstance(box, dict)
    }
    proc = store.get("procurement") or {}
    live = proc.get("current") if proc.get("current") is not None else proc.get("records", [])
    body["procurement"] = {"records": live}
    doc = {
        "format": FORMAT,
        "version": VERSION,
        "saved_at": (saved_at or datetime.now(UTC)).isoformat(timespec="seconds"),
        "app": {"sector": sector, "draft": bool(draft)},
        "store": _clean(body),
    }
    return json.dumps(doc, indent=2, ensure_ascii=False).encode("utf-8")


def filename(company: str, when: date | None = None) -> str:
    """``bee-check_<company>_<yyyy-mm-dd>.json`` with a safe company slug."""
    slug = _SLUG.sub("-", company or "").strip("-").lower()[:60] or "client"
    return f"bee-check_{slug}_{(when or datetime.now(UTC).date()).isoformat()}.json"


# ------------------------------------------------------------------ load
def _is_num(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool) and math.isfinite(v)


def _typed(default: Any, value: Any, where: str, problems: list[str]) -> Any:
    """``value`` if it has the same kind as ``default``; otherwise note it and keep default."""
    if value is None:
        return default if default is not None else None
    if isinstance(default, bool) or (default is None and isinstance(value, bool)):
        if isinstance(value, bool):
            return value
    elif isinstance(default, int | float) or default is None and _is_num(value):
        if _is_num(value):
            return float(value) if isinstance(default, float) else value
    elif isinstance(default, str) or default is None and isinstance(value, str):
        if isinstance(value, str):
            return value[:500]
    problems.append(f"{where} has an unexpected value and was reset.")
    return default


def _rows(value: Any, where: str, problems: list[str]) -> list[dict]:
    if not isinstance(value, list):
        problems.append(f"{where} is not a list of rows and was left empty.")
        return []
    if len(value) > MAX_ROWS:
        problems.append(f"{where} has more than {MAX_ROWS:,} rows; only the first were kept.")
    out = []
    for r in value[:MAX_ROWS]:
        if isinstance(r, dict):
            out.append(
                {
                    str(k)[:100]: (
                        v if v is None or isinstance(v, bool | str) or _is_num(v) else None
                    )
                    for k, v in r.items()
                }
            )
    return out


def _values(value: Any, problems: list[str]) -> dict:
    """values[mode][element][clause] = number | bool."""
    out: dict = {"rand": {}, "pct": {}}
    if not isinstance(value, dict):
        return out
    for mode in out:
        elems = value.get(mode) or {}
        if not isinstance(elems, dict):
            continue
        for el, clauses in elems.items():
            if not isinstance(clauses, dict):
                continue
            kept = {
                str(c): (bool(v) if isinstance(v, bool) else float(v))
                for c, v in clauses.items()
                if isinstance(v, bool) or _is_num(v)
            }
            dropped = len(clauses) - len(kept)
            if dropped:
                problems.append(
                    f"{dropped} indicator value(s) on {el} were not numbers and were left out."
                )
            out[mode][str(el)] = kept
    return out


def _date(v: Any) -> date | None:
    if isinstance(v, str):
        try:
            return date.fromisoformat(v[:10])
        except ValueError:
            return None
    return None


def parse(raw: bytes) -> tuple[dict, dict, list[str]]:
    """Return ``(store, app, notes)``. ``notes`` are non-fatal fixes made while loading.

    Raises ClientFileError when the file is not a client file at all.
    """
    if len(raw) > MAX_BYTES:
        raise ClientFileError([f"The file is larger than {MAX_BYTES // 1_000_000} MB."])
    try:
        doc = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ClientFileError(
            ["This is not a BEE Check client file (it is not valid JSON)."]
        ) from None
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        raise ClientFileError(["This is not a BEE Check client file."])
    ver = doc.get("version")
    if not isinstance(ver, int) or isinstance(ver, bool) or ver < 1:
        raise ClientFileError(["The file has no valid format version."])
    if ver > VERSION:
        raise ClientFileError(
            [f"This file was saved by a newer version of the app (format {ver}); update first."]
        )
    src = doc.get("store")
    if not isinstance(src, dict):
        raise ClientFileError(["The file has no calculation in it."])

    notes: list[str] = []
    store = fresh_store()
    for sec in _SCALAR_SECTIONS:
        given = src.get(sec) or {}
        if not isinstance(given, dict):
            notes.append(f"The {sec} section was unreadable and was reset.")
            continue
        for k, default in store[sec].items():
            if k in given:
                store[sec][k] = _typed(default, given[k], f"{sec}.{k}", notes)
    store["values"] = _values(src.get("values"), notes)
    for sec in _STRING_MAPS:
        given = src.get(sec) or {}
        if isinstance(given, dict):
            store[sec] = {str(k): v for k, v in given.items() if isinstance(v, str)}
    for sec in _NUMBER_MAPS:
        given = src.get(sec) or {}
        if isinstance(given, dict):
            store[sec] = {
                str(el): {str(g): float(v) for g, v in grp.items() if _is_num(v)}
                for el, grp in given.items()
                if isinstance(grp, dict)
            }
    opts = src.get("options")
    if isinstance(opts, dict):
        store["options"] = {
            str(k): v
            for k, v in opts.items()
            if v is None or isinstance(v, bool | str) or _is_num(v)
        }
    proc = src.get("procurement")
    if isinstance(proc, dict):
        store["procurement"] = {
            "records": _rows(proc.get("records", []), "Supplier list", notes),
            "version": 0,
        }
    contrib = src.get("contributions")
    if isinstance(contrib, dict):
        for el, box in contrib.items():
            if not isinstance(box, dict):
                continue
            live = box.get("current") if box.get("current") is not None else box.get("records", [])
            rows = _rows(live, f"Contributions ({el})", notes)
            store["contributions"][str(el)] = {"records": rows, "version": 0, "current": None}
    nv = src.get("net_value")
    if isinstance(nv, dict):
        for el, box in nv.items():
            if not isinstance(box, dict):
                continue
            kept: dict = {}
            for k, v in box.items():
                if k in _DATE_KEYS:
                    kept[k] = _date(v)
                elif _is_num(v):
                    kept[k] = float(v)
                elif v is None:
                    kept[k] = None
            store["net_value"][str(el)] = kept

    app = doc.get("app") if isinstance(doc.get("app"), dict) else {}
    app_out = {
        "sector": app.get("sector") if isinstance(app.get("sector"), str) else None,
        "draft": app.get("draft") is True,
        "saved_at": doc.get("saved_at") if isinstance(doc.get("saved_at"), str) else None,
    }
    return store, app_out, notes
