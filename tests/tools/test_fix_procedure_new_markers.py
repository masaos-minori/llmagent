"""tests/tools/test_fix_procedure_new_markers.py
Tests for tools/fix_procedure_new_markers.py: marker insertion, `--dry-run`, exit codes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import tools.fix_procedure_new_markers as fpm

TEXT = "Create `alpha` and `beta`.\nSee `alpha` (new) and 日本 ünï.\n"
FIXED = "Create `alpha` (new) and `beta`.\nSee `alpha` (new) and 日本 ünï.\n"


def _doc(tmp_path: Path) -> Path:
    path = tmp_path / "p.md"
    path.write_text(TEXT, encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_add_markers_skips_already_marked_names() -> None:
    assert fpm.add_markers(TEXT, ["alpha"]) == (FIXED, 1)


def test_real_run_adds_markers_and_writes_utf8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = _doc(tmp_path)

    assert fpm.main(["--symbols", "alpha", str(doc)]) == 0

    assert doc.read_bytes() == FIXED.encode()
    assert "1 marker(s) added" in capsys.readouterr().out
    assert [p.name for p in tmp_path.iterdir()] == ["p.md"]


def test_dry_run_leaves_the_file_unchanged_and_prints_the_diff(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = _doc(tmp_path)
    before = _sha(doc)

    assert fpm.main(["--symbols", "alpha", str(doc), "--dry-run"]) == 0

    out = capsys.readouterr().out
    assert _sha(doc) == before
    assert "+Create `alpha` (new) and `beta`." in out
    assert "1 marker(s) added" in out


def test_missing_file_returns_one_in_both_modes(tmp_path: Path) -> None:
    missing = str(tmp_path / "none.md")

    assert fpm.main(["--symbols", "alpha", missing]) == 1
    assert fpm.main(["--symbols", "alpha", missing, "--dry-run"]) == 1
