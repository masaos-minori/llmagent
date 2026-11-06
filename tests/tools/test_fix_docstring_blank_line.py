"""tests/tools/test_fix_docstring_blank_line.py
Regression tests for tools/fix_docstring_blank_line.py around its atomic write:
`--dry-run` writes nothing, the real run fixes a docstring as UTF-8, unchanged files
are left alone.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

import tools.fix_docstring_blank_line as fdb

BROKEN = '"""Summary line.\nMore detail ünï 日本.\n"""\nX = 1\n'
FIXED = '"""Summary line.\n\nMore detail ünï 日本.\n"""\nX = 1\n'
CLEAN = '"""One line."""\nX = 1\n'


def _run(monkeypatch: pytest.MonkeyPatch, directory: Path, *flags: str) -> None:
    monkeypatch.setattr(sys, "argv", ["prog", "--dir", str(directory), *flags])
    fdb.main()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_fix_d205_inserts_the_blank_line() -> None:
    assert fdb.fix_d205(BROKEN) == (FIXED, [1])


def test_fix_d205_leaves_a_single_line_docstring() -> None:
    assert fdb.fix_d205(CLEAN) == (CLEAN, [])


def test_dry_run_prints_and_writes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "m.py"
    target.write_text(BROKEN, encoding="utf-8")
    before = _sha(target)

    _run(monkeypatch, tmp_path, "--dry-run")

    assert "[DRY-RUN]" in capsys.readouterr().out
    assert _sha(target) == before


def test_real_run_fixes_the_docstring_and_writes_utf8(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "m.py"
    target.write_text(BROKEN, encoding="utf-8")

    _run(monkeypatch, tmp_path)

    assert target.read_bytes() == FIXED.encode()
    assert "1 fixes" in capsys.readouterr().out
    assert [p.name for p in tmp_path.iterdir()] == ["m.py"]


def test_a_file_without_changes_is_not_rewritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "m.py"
    target.write_text(CLEAN, encoding="utf-8")
    before = target.stat().st_mtime_ns

    _run(monkeypatch, tmp_path)

    assert target.stat().st_mtime_ns == before
