"""Tests for tools/check_tool_descriptions_sync.py CI/hook reference check."""

from __future__ import annotations

from pathlib import Path

from tools.check_tool_descriptions_sync import find_dangling_config_references


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_reports_only_references_to_missing_tools(tmp_path: Path) -> None:
    _write(tmp_path / "tools" / "check_a.py", "")
    _write(
        tmp_path / ".github" / "workflows" / "w.yml",
        'paths:\n  - "tools/check_a.py"\n  - "tools/check_gone.py"\n'
        "run: python tools/check_old.py docs/x.md\n",
    )
    _write(
        tmp_path / ".pre-commit-config.yaml",
        "entry: python -m tools.check_a\nentry: python -m tools.check_moved\n",
    )
    _write(tmp_path / "tox.ini", "uv run python tools/check_a.py\n")

    assert find_dangling_config_references(tmp_path) == [
        (".github/workflows/w.yml", 3, "check_gone.py"),
        (".github/workflows/w.yml", 4, "check_old.py"),
        (".pre-commit-config.yaml", 2, "check_moved.py"),
    ]


def test_no_config_files_yields_no_findings(tmp_path: Path) -> None:
    _write(tmp_path / "tools" / "check_a.py", "")

    assert find_dangling_config_references(tmp_path) == []


def test_repository_configuration_has_no_dangling_references() -> None:
    assert find_dangling_config_references() == []
