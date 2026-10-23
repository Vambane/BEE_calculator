"""Offline checks for tools/live_smoke.py (does not hit production)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "tools" / "live_smoke.py"


def test_live_smoke_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as ei:
        sys.argv = [str(SCRIPT), "--help"]
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert ei.value.code == 0
    out = capsys.readouterr().out
    assert "live" in out.lower() or "url" in out.lower() or "BEE" in out


def test_live_smoke_markers_include_app_and_shell():
    ns = runpy.run_path(str(SCRIPT), run_name="not_main")
    markers = ns["MARKERS"]
    assert "BEE Check" in markers
    assert "Privacy" in markers
    assert "streamlitAppPage" in markers
