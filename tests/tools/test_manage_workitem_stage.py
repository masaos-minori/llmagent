"""tests/tools/test_manage_workitem_stage.py
Tests for tools/manage_workitem_stage.py.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

import git
import pytest

from tools.manage_workitem_stage import (
    build_parser,
    cmd_close_implementation,
    cmd_close_issue,
    cmd_close_plan,
)

# Well-formed `### Execution Status` table matching
# `templates/execution-status.md`'s column structure, with one `Pending` row.
EXECUTION_STATUS_PENDING = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Do the thing | Pending | — | — | |
"""

# Same table structure, all rows `Completed` — no block expected.
EXECUTION_STATUS_COMPLETED = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Do the thing | Completed | 20260101-000000 | 20260101-000100 | |
"""

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Path:
    """Build a temporary `git init`'d repository with workflow-stage trees.

    Pre-creates `issues/done/`, `plans/done/`, and `implementations/done/` on
    disk (mirroring the real repository's layout) — `git mv` refuses to move a
    file into a destination directory that does not already exist on disk, so
    a fixture without these would make every success-path move fail.
    """
    for stage in ("issues", "plans", "implementations"):
        (tmp_path / stage / "done").mkdir(parents=True)

    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as writer:
        writer.set_value("user", "name", "Test User")
        writer.set_value("user", "email", "test@example.com")

    keep = tmp_path / ".gitkeep"
    keep.write_text("", encoding="utf-8")
    repo.index.add([str(keep)])
    repo.index.commit("initial commit")
    return tmp_path


def _commit_file(repo: git.Repo, path: Path, content: str) -> None:
    """Write `content` to `path` and commit it, so it starts with no local diff.

    A `move_to_done` call on an uncommitted file is out of this file's scope
    (see the Plan's Details) — every fixture file must be committed first.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    repo.index.add([str(path)])
    repo.index.commit(f"add {path.name}")


SIMPLE_MOVE_CASES: list[tuple[str, str, Callable[[argparse.Namespace], int]]] = [
    ("close-issue", "issues", cmd_close_issue),
    ("close-plan", "plans", cmd_close_plan),
]
SIMPLE_MOVE_IDS = [case[0] for case in SIMPLE_MOVE_CASES]


# ---------------------------------------------------------------------------
# close-issue / close-plan: success path (REQ-001, REQ-002, REQ-005,
# REQ-006; AC-1)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
def test_simple_move_success(
    temp_git_repo: Path,
    capsys: pytest.CaptureFixture[str],
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / stage_dir / "20260101_fixture.md"
    content = "# Fixture\n\nSome content.\n"
    _commit_file(repo, source, content)
    content_before = source.read_bytes()

    args = build_parser().parse_args([subcommand, str(source)])
    exit_code = cmd_func(args)

    destination = temp_git_repo / stage_dir / "done" / "20260101_fixture.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()
    # REQ-005: the tool must not rewrite file content during the move.
    assert destination.read_bytes() == content_before

    # AC-1: git records the move as a rename, not a delete+add.
    status = repo.git.status("--porcelain")
    assert "R  " in status
    assert source.relative_to(temp_git_repo).as_posix() in status
    assert destination.relative_to(temp_git_repo).as_posix() in status

    # REQ-006: the printed result includes the resulting path.
    captured = capsys.readouterr()
    assert str(destination) in captured.out


# ---------------------------------------------------------------------------
# close-issue / close-plan: refusal paths (REQ-001, REQ-002)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
def test_simple_move_missing_source_refuses(
    temp_git_repo: Path,
    capsys: pytest.CaptureFixture[str],
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    source = temp_git_repo / stage_dir / "does_not_exist.md"

    args = build_parser().parse_args([subcommand, str(source)])
    exit_code = cmd_func(args)

    assert exit_code == 1
    assert not (temp_git_repo / stage_dir / "done" / "does_not_exist.md").exists()

    # REQ-006: the printed result reflects the failure exit code.
    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert str(source) in captured.err


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
def test_simple_move_existing_destination_refuses(
    temp_git_repo: Path,
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / stage_dir / "20260102_dup.md"
    _commit_file(repo, source, "content\n")

    destination = temp_git_repo / stage_dir / "done" / "20260102_dup.md"
    destination.write_text("already there\n", encoding="utf-8")

    args = build_parser().parse_args([subcommand, str(source)])
    exit_code = cmd_func(args)

    assert exit_code == 1
    assert source.exists()
    assert destination.read_text(encoding="utf-8") == "already there\n"


# ---------------------------------------------------------------------------
# close-implementation: success path with no Pending rows (third
# subcommand's success case, per the Plan's Goal)
# ---------------------------------------------------------------------------


def test_close_implementation_success_without_pending_rows(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "implementations" / "20260103_completed.md"
    _commit_file(repo, source, EXECUTION_STATUS_COMPLETED)
    content_before = source.read_bytes()

    args = build_parser().parse_args(["close-implementation", str(source)])
    exit_code = cmd_close_implementation(args)

    destination = temp_git_repo / "implementations" / "done" / "20260103_completed.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()
    assert destination.read_bytes() == content_before

    status = repo.git.status("--porcelain")
    assert "R  " in status

    captured = capsys.readouterr()
    assert str(destination) in captured.out


# ---------------------------------------------------------------------------
# close-implementation: blocked-Pending case (REQ-003; AC-2)
# ---------------------------------------------------------------------------


def test_close_implementation_pending_row_blocks_move(temp_git_repo: Path) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "implementations" / "20260104_pending.md"
    _commit_file(repo, source, EXECUTION_STATUS_PENDING)
    content_before = source.read_bytes()

    args = build_parser().parse_args(["close-implementation", str(source)])
    exit_code = cmd_close_implementation(args)

    assert exit_code == 1
    assert source.exists()
    # File was not moved, and its content is untouched.
    assert source.read_bytes() == content_before
    destination = temp_git_repo / "implementations" / "done" / "20260104_pending.md"
    assert not destination.exists()


def test_close_implementation_pending_row_error_names_step(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "implementations" / "20260105_pending.md"
    _commit_file(repo, source, EXECUTION_STATUS_PENDING)

    args = build_parser().parse_args(["close-implementation", str(source)])
    exit_code = cmd_close_implementation(args)

    assert exit_code == 1
    captured = capsys.readouterr()
    # The blocking row's Step/Description are named in the result.
    assert "Step 1" in captured.err
    assert "Do the thing" in captured.err


# ---------------------------------------------------------------------------
# close-implementation: forced override (REQ-004, REQ-005, REQ-006; AC-3)
# ---------------------------------------------------------------------------


def test_close_implementation_force_and_reason_overrides_pending_block(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "implementations" / "20260106_forced.md"
    _commit_file(repo, source, EXECUTION_STATUS_PENDING)
    content_before = source.read_bytes()

    args = build_parser().parse_args(
        [
            "close-implementation",
            str(source),
            "--force",
            "--reason",
            "test override",
        ]
    )
    exit_code = cmd_close_implementation(args)

    destination = temp_git_repo / "implementations" / "done" / "20260106_forced.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()
    # REQ-005: content is byte-for-byte identical after the forced move.
    assert destination.read_bytes() == content_before

    # AC-3 / REQ-006: printed result includes both the resulting path and
    # the supplied reason string.
    captured = capsys.readouterr()
    assert str(destination) in captured.out
    assert "test override" in captured.out
