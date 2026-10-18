"""Tests for tools/fix_docstring_paths.py output format."""

from __future__ import annotations

from pathlib import Path

from tools.check_docstrings import check_docstring
from tools.fix_docstring_paths import process_file


def _write(root: Path, rel: str, text: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_prose_header_becomes_path_dash_description(tmp_path: Path) -> None:
    path = _write(
        tmp_path,
        "pkg/mod.py",
        '"""Schema layer: definitions.\n\nMore detail.\n"""\n\nX = 1\n',
    )
    assert process_file(path, tmp_path, apply=True) is not None
    text = path.read_text(encoding="utf-8")
    assert text.startswith(
        '"""scripts/pkg/mod.py — Schema layer: definitions.\n\nMore detail.'
    )
    assert check_docstring(path, "pkg/mod.py") == []


def test_dry_run_does_not_write(tmp_path: Path) -> None:
    source = '"""Schema layer."""\n'
    path = _write(tmp_path, "mod.py", source)
    assert process_file(path, tmp_path, apply=False) is not None
    assert path.read_text(encoding="utf-8") == source


def test_stale_path_is_rewritten_inline(tmp_path: Path) -> None:
    path = _write(tmp_path, "pkg/mod.py", '"""mod.py — Does things."""\n')
    process_file(path, tmp_path, apply=True)
    assert path.read_text(encoding="utf-8").startswith(
        '"""scripts/pkg/mod.py — Does things.'
    )


def test_missing_docstring_is_skipped_not_invented(tmp_path: Path) -> None:
    source = "X = 1\n"
    path = _write(tmp_path, "mod.py", source)
    result = process_file(path, tmp_path, apply=True)
    assert result is not None and result.startswith("SKIP")
    assert path.read_text(encoding="utf-8") == source


def test_header_with_em_dash_is_skipped(tmp_path: Path) -> None:
    source = '"""Registry — shared schema."""\n'
    path = _write(tmp_path, "mod.py", source)
    result = process_file(path, tmp_path, apply=True)
    assert result is not None and result.startswith("SKIP")
    assert path.read_text(encoding="utf-8") == source


def test_rerun_after_fix_is_noop(tmp_path: Path) -> None:
    path = _write(tmp_path, "mod.py", '"""Schema layer."""\n')
    process_file(path, tmp_path, apply=True)
    assert process_file(path, tmp_path, apply=True) is None
