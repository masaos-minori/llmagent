"""tests/tools/test_atomic_write.py
Tests for tools/_atomic_write.py: atomic and staged writes, the diff preview, and the
`--dry-run` option helper.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import stat
from pathlib import Path

import pytest

from tools import _atomic_write
from tools._atomic_write import (
    add_dry_run_argument,
    atomic_write_text,
    print_dry_run,
    render_diff,
    stage_write,
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _leftovers(directory: Path, keep: str) -> list[str]:
    return sorted(p.name for p in directory.iterdir() if p.name != keep)


def test_success_writes_utf8_bytes(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"

    atomic_write_text(target, "ünï 日本\n")

    assert target.read_bytes() == "ünï 日本\n".encode()
    assert _leftovers(tmp_path, "a.txt") == []


def test_explicit_encoding_is_honoured(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"

    atomic_write_text(target, "é", encoding="latin-1")

    assert target.read_bytes() == b"\xe9"


def test_existing_file_mode_is_preserved(tmp_path: Path) -> None:
    target = tmp_path / "script.sh"
    target.write_text("old\n", encoding="utf-8")
    target.chmod(0o755)

    atomic_write_text(target, "new\n")

    assert stat.S_IMODE(target.stat().st_mode) == 0o755
    assert target.read_text(encoding="utf-8") == "new\n"


def test_new_file_gets_the_default_mode_not_0600(tmp_path: Path) -> None:
    target = tmp_path / "new.txt"
    previous = os.umask(0o022)
    try:
        atomic_write_text(target, "x")
    finally:
        os.umask(previous)

    assert stat.S_IMODE(target.stat().st_mode) == 0o644


def test_line_endings_and_missing_trailing_newline_are_preserved(
    tmp_path: Path,
) -> None:
    target = tmp_path / "a.txt"

    atomic_write_text(target, "a\r\nb")

    assert target.read_bytes() == b"a\r\nb"


def test_interruption_before_replace_leaves_the_original_and_no_temp_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "a.txt"
    target.write_text("original\n", encoding="utf-8")
    before = _sha(target)

    def boom(*_: object, **__: object) -> None:
        raise OSError("replace failed")

    monkeypatch.setattr(_atomic_write.os, "replace", boom)
    with pytest.raises(OSError, match="replace failed"):
        atomic_write_text(target, "changed\n")

    assert _sha(target) == before
    assert _leftovers(tmp_path, "a.txt") == []


def test_staged_write_changes_nothing_until_commit(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"
    target.write_text("old\n", encoding="utf-8")

    staged = stage_write(target, "new\n")
    assert target.read_text(encoding="utf-8") == "old\n"

    staged.commit()
    assert target.read_text(encoding="utf-8") == "new\n"
    assert _leftovers(tmp_path, "a.txt") == []


def test_staged_write_discard_removes_the_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "a.txt"

    stage_write(target, "x").discard()

    assert _leftovers(tmp_path, "") == []
    assert not target.exists()


def test_discard_is_idempotent(tmp_path: Path) -> None:
    staged = stage_write(tmp_path / "a.txt", "x")

    staged.discard()
    staged.discard()


def test_render_diff_for_change_no_change_and_new_file(tmp_path: Path) -> None:
    path = tmp_path / "a.txt"

    changed = render_diff(path, "a\nb\n", "a\nc\n")
    assert f"--- a/{path}" in changed
    assert "-b" in changed
    assert "+c" in changed
    assert render_diff(path, "same\n", "same\n") == ""
    assert "+only\n" in render_diff(path, "", "only\n")


def test_print_dry_run_writes_nothing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "a.txt"
    target.write_text("old\n", encoding="utf-8")
    before = _sha(target)

    print_dry_run(target, "old\n", "new\n")

    assert "+new" in capsys.readouterr().out
    assert _sha(target) == before
    assert _leftovers(tmp_path, "a.txt") == []


def test_print_dry_run_reports_no_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    print_dry_run(tmp_path / "a.txt", "x\n", "x\n")

    assert "no change" in capsys.readouterr().out


def test_dry_run_option_defaults_to_false_and_is_a_flag() -> None:
    parser = argparse.ArgumentParser()
    add_dry_run_argument(parser)

    assert parser.parse_args([]).dry_run is False
    assert parser.parse_args(["--dry-run"]).dry_run is True
