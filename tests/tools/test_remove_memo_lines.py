"""tests/tools/test_remove_memo_lines.py
Tests for tools/remove_memo_lines.py: removing the completed procedure lines from a memo list.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parent.parent.parent / "tools" / "remove_memo_lines.py"

PREFIX = "implementations/20261126-225455_"


@pytest.fixture(autouse=True)
def _cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Run each test from its own directory, restored afterwards so no later test inherits it."""
    monkeypatch.chdir(tmp_path)
    yield


def _memo(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "memo.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _run(
    memo: Path, prefix: str, dry_run: bool = False
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(TOOL), str(memo), "--prefix", prefix]
    if dry_run:
        cmd.append("--dry-run")
    return subprocess.run(cmd, capture_output=True, text=True)


def _archived(tmp_path: Path, name: str) -> None:
    done = tmp_path / "implementations/done"
    done.mkdir(parents=True, exist_ok=True)
    (done / name).write_text("x", encoding="utf-8")


def test_removes_only_when_every_matched_procedure_is_archived(tmp_path: Path) -> None:
    memo = _memo(
        tmp_path,
        [
            "header",
            "- implementations/20261126-225455_01_a.py.md",
            "- implementations/20261126-230743_01_c.py.md",
        ],
    )
    _archived(tmp_path, "20261126-225455_01_a.py.md")

    code = _run(memo, PREFIX)

    assert code.returncode == 0
    remaining = memo.read_text(encoding="utf-8")
    assert "225455" not in remaining
    assert "230743" in remaining


def test_a_pending_match_removes_nothing(tmp_path: Path) -> None:
    memo = _memo(tmp_path, ["- implementations/20261126-225455_02_b.py.md"])
    pending = tmp_path / "implementations"
    pending.mkdir(parents=True)
    (pending / "20261126-225455_02_b.py.md").write_text("x", encoding="utf-8")

    code = _run(memo, PREFIX)

    assert code.returncode == 1
    assert "not archived" in code.stderr
    assert "225455" in memo.read_text(encoding="utf-8")


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    memo = _memo(tmp_path, ["- implementations/20261126-225455_01_a.py.md"])
    _archived(tmp_path, "20261126-225455_01_a.py.md")

    code = _run(memo, PREFIX, dry_run=True)

    assert code.returncode == 0
    assert "225455" in memo.read_text(encoding="utf-8")
    assert "-" in code.stdout


def test_no_matching_line_exits_1(tmp_path: Path) -> None:
    memo = _memo(tmp_path, ["header"])

    code = _run(memo, PREFIX)

    assert code.returncode == 1
    assert "no line matches" in code.stderr
