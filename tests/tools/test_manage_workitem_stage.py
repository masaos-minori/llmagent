"""tests/tools/test_manage_workitem_stage.py
Tests for tools/manage_workitem_stage.py.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

import git
import git.exc
import pytest

from tools.manage_workitem_stage import _find_remote_conflict as find_remote_conflict
from tools.manage_workitem_stage import _run_with_lock_retry as run_with_lock_retry
from tools.manage_workitem_stage import (
    build_parser,
    cmd_close_implementation,
    cmd_close_issue,
    cmd_close_plan,
    move_to_done,
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

# Same heading and row structure, but the `Status` column has been renamed —
# a template drift that must not silently disable the Pending-row block.
EXECUTION_STATUS_RENAMED_STATUS_COLUMN = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | State | Started | Completed | Notes |
|------|-------------|-------|---------|-----------|-------|
| 1 | Do the thing | Pending | — | — | |
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

    Used by the success-path fixtures below; see the "uncommitted changes"
    tests further down for the refusal paths this deliberately avoids here.
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
# close-issue / close-plan: uncommitted-changes refusal
# ---------------------------------------------------------------------------


def _dirty_untracked(repo: git.Repo, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("untracked content\n", encoding="utf-8")


def _dirty_staged(repo: git.Repo, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("staged content\n", encoding="utf-8")
    repo.index.add([str(path)])


def _dirty_modified_after_commit(repo: git.Repo, path: Path) -> None:
    _commit_file(repo, path, "original content\n")
    path.write_text("modified content\n", encoding="utf-8")


UNCOMMITTED_CASES: list[tuple[str, Callable[[git.Repo, Path], None]]] = [
    ("untracked", _dirty_untracked),
    ("staged", _dirty_staged),
    ("modified-after-commit", _dirty_modified_after_commit),
]
UNCOMMITTED_IDS = [case[0] for case in UNCOMMITTED_CASES]


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
@pytest.mark.parametrize(
    ("change_kind", "make_dirty"), UNCOMMITTED_CASES, ids=UNCOMMITTED_IDS
)
def test_simple_move_uncommitted_source_refuses(
    temp_git_repo: Path,
    capsys: pytest.CaptureFixture[str],
    change_kind: str,
    make_dirty: Callable[[git.Repo, Path], None],
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / stage_dir / "20260107_dirty.md"
    make_dirty(repo, source)

    args = build_parser().parse_args([subcommand, str(source)])
    exit_code = cmd_func(args)

    destination = temp_git_repo / stage_dir / "done" / "20260107_dirty.md"
    assert exit_code == 1
    assert source.exists()
    assert not destination.exists()

    captured = capsys.readouterr()
    assert "uncommitted changes" in captured.err
    assert str(source) in captured.err


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
def test_simple_move_ignores_unrelated_uncommitted_file(
    temp_git_repo: Path,
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    """An uncommitted change to a *different* file must not block the move —
    the uncommitted-changes check is scoped to the source path alone."""
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / stage_dir / "20260108_clean.md"
    _commit_file(repo, source, "clean content\n")

    unrelated = temp_git_repo / stage_dir / "20260108_unrelated.md"
    _commit_file(repo, unrelated, "will be dirtied\n")
    unrelated.write_text("dirtied\n", encoding="utf-8")

    args = build_parser().parse_args([subcommand, str(source)])
    exit_code = cmd_func(args)

    destination = temp_git_repo / stage_dir / "done" / "20260108_clean.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()


# ---------------------------------------------------------------------------
# close-plan: --allow-uncommitted bypass and its diagnostic hint (item 6
# friction-reduction -- a routine Plan self-correction landing in the same
# cycle as close-plan should not require a separate ask-the-user-to-commit
# round trip)
# ---------------------------------------------------------------------------


def test_close_plan_allow_uncommitted_bypasses_refusal(
    temp_git_repo: Path,
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "plans" / "20260109_dirty.md"
    _dirty_modified_after_commit(repo, source)

    args = build_parser().parse_args(["close-plan", str(source), "--allow-uncommitted"])
    exit_code = cmd_close_plan(args)

    destination = temp_git_repo / "plans" / "done" / "20260109_dirty.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == "modified content\n"


def test_close_plan_refusal_shows_diff_for_unstaged_modification(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """`git diff --cached` alone reports empty for an unstaged working-tree
    edit -- the far more common case a routine self-correction produces --
    so the hint must fall back to `git diff HEAD` to actually show it.
    """
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "plans" / "20260110_dirty.md"
    _dirty_modified_after_commit(repo, source)

    args = build_parser().parse_args(["close-plan", str(source)])
    exit_code = cmd_close_plan(args)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "--allow-uncommitted" in captured.err
    assert "-original content" in captured.err
    assert "+modified content" in captured.err


def test_close_plan_refusal_shows_diff_for_staged_modification(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "plans" / "20260111_dirty.md"
    _dirty_staged(repo, source)

    args = build_parser().parse_args(["close-plan", str(source)])
    exit_code = cmd_close_plan(args)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "+staged content" in captured.err


def test_close_plan_refusal_notes_untracked_file_has_no_diff(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "plans" / "20260112_dirty.md"
    _dirty_untracked(repo, source)

    args = build_parser().parse_args(["close-plan", str(source)])
    exit_code = cmd_close_plan(args)

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "untracked file" in captured.err


# ---------------------------------------------------------------------------
# move_to_done: missing archive directory
# ---------------------------------------------------------------------------


def test_move_to_done_missing_archive_directory_refuses(tmp_path: Path) -> None:
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as writer:
        writer.set_value("user", "name", "Test User")
        writer.set_value("user", "email", "test@example.com")

    source = tmp_path / "plans" / "20260109_no_done_dir.md"
    source.parent.mkdir(parents=True)
    source.write_text("content\n", encoding="utf-8")
    repo.index.add([str(source)])
    repo.index.commit("add plan without a done/ directory")
    # plans/done/ is deliberately not created.

    result = move_to_done(source)

    assert result.success is False
    assert result.error is not None
    assert "archive directory does not exist" in result.error
    assert source.exists()


# ---------------------------------------------------------------------------
# _run_with_lock_retry: git index-lock contention
# ---------------------------------------------------------------------------


def _lock_contention_error() -> git.exc.GitCommandError:
    return git.exc.GitCommandError(
        ["git", "mv", "a", "b"],
        128,
        stderr="fatal: Unable to create '/repo/.git/index.lock': File exists.",
    )


def _unrelated_git_error() -> git.exc.GitCommandError:
    return git.exc.GitCommandError(
        ["git", "mv", "a", "b"], 128, stderr="fatal: bad object HEAD"
    )


@pytest.fixture(autouse=True)
def _no_retry_delay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero out the retry delay for every test in this file — none of them
    depend on real elapsed time, and this keeps the suite fast."""
    import tools.manage_workitem_stage as workitem_stage_module

    monkeypatch.setattr(workitem_stage_module, "_LOCK_RETRY_DELAY_SECONDS", 0)


def test_run_with_lock_retry_succeeds_after_transient_contention() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 3:
            raise _lock_contention_error()
        return "ok"

    assert run_with_lock_retry(flaky) == "ok"
    assert calls["n"] == 3


def test_run_with_lock_retry_exhausts_attempts_and_raises() -> None:
    import tools.manage_workitem_stage as workitem_stage_module

    calls = {"n": 0}

    def always_locked() -> str:
        calls["n"] += 1
        raise _lock_contention_error()

    with pytest.raises(git.exc.GitCommandError):
        run_with_lock_retry(always_locked)
    assert calls["n"] == workitem_stage_module._LOCK_RETRY_ATTEMPTS


def test_run_with_lock_retry_does_not_retry_unrelated_error() -> None:
    calls = {"n": 0}

    def unrelated_failure() -> str:
        calls["n"] += 1
        raise _unrelated_git_error()

    with pytest.raises(git.exc.GitCommandError):
        run_with_lock_retry(unrelated_failure)
    assert calls["n"] == 1


# ---------------------------------------------------------------------------
# _find_remote_conflict: no remote configured
# ---------------------------------------------------------------------------


def test_find_remote_conflict_no_remote_returns_none(temp_git_repo: Path) -> None:
    repo = git.Repo(temp_git_repo)
    destination = temp_git_repo / "plans" / "done" / "whatever.md"
    assert find_remote_conflict(repo, destination) is None


# ---------------------------------------------------------------------------
# _find_remote_conflict / close-plan: remote already has the destination
# (two sessions sharing one remote, no real network involved)
# ---------------------------------------------------------------------------


@pytest.fixture
def remote_conflict_repos(tmp_path: Path) -> tuple[Path, Path]:
    """A bare `origin` plus two clones (`session_a`, `session_b`) that both start
    from an identical initial commit containing the workflow-stage `done/`
    directories and one already-committed, already-pushed plan file.

    Simulates two concurrent sessions sharing one remote, to exercise
    `_find_remote_conflict`'s detection with no real network access (the
    "remote" is a local bare repository).
    """
    bare_path = tmp_path / "origin.git"
    git.Repo.init(str(bare_path), bare=True)

    seed_path = tmp_path / "seed"
    gitkeep_paths = []
    for stage in ("issues", "plans", "implementations"):
        done_dir = seed_path / stage / "done"
        done_dir.mkdir(parents=True)
        gitkeep = done_dir / ".gitkeep"
        gitkeep.write_text("", encoding="utf-8")
        gitkeep_paths.append(str(gitkeep))
    seed_repo = git.Repo.init(seed_path)
    with seed_repo.config_writer() as writer:
        writer.set_value("user", "name", "Test User")
        writer.set_value("user", "email", "test@example.com")
    # Git does not track empty directories — each done/.gitkeep must be
    # committed so `git clone` below actually recreates the done/ directory.
    seed_repo.index.add(gitkeep_paths)
    seed_repo.index.commit("initial commit")

    plan_path = seed_path / "plans" / "20260110_shared.md"
    plan_path.write_text("shared plan content\n", encoding="utf-8")
    seed_repo.index.add([str(plan_path)])
    seed_repo.index.commit("add shared plan")

    branch = seed_repo.active_branch.name
    seed_repo.create_remote("origin", str(bare_path))
    seed_repo.remote("origin").push(f"{branch}:{branch}")

    def _clone(name: str) -> Path:
        dest = tmp_path / name
        cloned = git.Repo.clone_from(str(bare_path), str(dest))
        with cloned.config_writer() as writer:
            writer.set_value("user", "name", "Test User")
            writer.set_value("user", "email", "test@example.com")
        return dest

    return _clone("session_a"), _clone("session_b")


def test_close_plan_detects_conflict_already_archived_on_remote(
    remote_conflict_repos: tuple[Path, Path],
) -> None:
    session_a, session_b = remote_conflict_repos
    plan_name = "20260110_shared.md"

    # session_b archives the shared plan and pushes first.
    session_b_repo = git.Repo(session_b)
    branch = session_b_repo.active_branch.name
    result_b = move_to_done(session_b / "plans" / plan_name)
    assert result_b.success
    session_b_repo.index.commit("archive shared plan (session_b)")
    session_b_repo.remote("origin").push(f"{branch}:{branch}")

    # session_a never fetched since cloning: its local plans/done/ does not
    # yet have the file, but origin now does.
    source_a = session_a / "plans" / plan_name
    destination_a = session_a / "plans" / "done" / plan_name
    assert source_a.exists()
    assert not destination_a.exists()

    result_a = move_to_done(source_a)

    assert result_a.success is False
    assert result_a.error is not None
    assert "already exists on origin/" in result_a.error
    assert source_a.exists()
    assert not destination_a.exists()


def test_close_plan_with_remote_configured_but_no_conflict_succeeds(
    remote_conflict_repos: tuple[Path, Path],
) -> None:
    session_a, _session_b = remote_conflict_repos
    plan_name = "20260110_shared.md"

    # No concurrent archival happened on the remote for this file — fetching
    # and checking must not false-positive block a normal move.
    result = move_to_done(session_a / "plans" / plan_name)

    assert result.success is True
    assert not (session_a / "plans" / plan_name).exists()
    assert (session_a / "plans" / "done" / plan_name).exists()


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


# ---------------------------------------------------------------------------
# close-implementation: renamed/missing `Status` column must error, not
# silently skip the Pending-row block
# ---------------------------------------------------------------------------


def test_close_implementation_renamed_status_column_errors_instead_of_silently_passing(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / "implementations" / "20260111_renamed_column.md"
    _commit_file(repo, source, EXECUTION_STATUS_RENAMED_STATUS_COLUMN)

    args = build_parser().parse_args(["close-implementation", str(source)])
    exit_code = cmd_close_implementation(args)

    assert exit_code == 1
    assert source.exists()
    destination = (
        temp_git_repo / "implementations" / "done" / "20260111_renamed_column.md"
    )
    assert not destination.exists()

    captured = capsys.readouterr()
    assert "Status" in captured.err
    assert "missing or malformed" in captured.err
