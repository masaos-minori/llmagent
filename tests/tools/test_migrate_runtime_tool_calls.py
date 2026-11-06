"""tests/tools/test_migrate_runtime_tool_calls.py
Tests for tools/migrate_runtime_tool_calls.py: rewrite, `--dry-run`, and the syntax-error
refusal, each with the same exit code in both modes.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import tools.migrate_runtime_tool_calls as mig

SOURCE = (
    "from shared.runtime_tool import build_runtime_tool\n\n"
    "# ünï 日本\n"
    "tool = build_runtime_tool(1, 2, 3, 4, 5, 6)\n"
)


def _file(tmp_path: Path, text: str = SOURCE) -> Path:
    path = tmp_path / "test_x.py"
    path.write_text(text, encoding="utf-8")
    return path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_real_run_renames_the_call_and_writes_utf8(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _file(tmp_path)

    assert mig.main([str(path)]) == 0

    text = path.read_bytes().decode("utf-8")
    assert "build_fixture_runtime_tool(1, 2, 3, 4, 5, 6)" in text
    assert "ünï 日本" in text
    assert "calls=1 renamed=1" in capsys.readouterr().out
    assert [p.name for p in tmp_path.iterdir()] == ["test_x.py"]


def test_dry_run_leaves_the_file_unchanged_and_returns_the_real_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = _file(tmp_path)
    before = _sha(path)

    assert mig.main([str(path), "--dry-run"]) == 0

    assert _sha(path) == before
    assert "+tool = build_fixture_runtime_tool(" in capsys.readouterr().out


def test_unparsable_source_raises_and_is_left_unchanged_in_both_modes(
    tmp_path: Path,
) -> None:
    path = _file(tmp_path, "def broken(:\n")

    with pytest.raises(SyntaxError):
        mig.main([str(path)])
    with pytest.raises(SyntaxError):
        mig.main([str(path), "--dry-run"])
    assert path.read_text(encoding="utf-8") == "def broken(:\n"
