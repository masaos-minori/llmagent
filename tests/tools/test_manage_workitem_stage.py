"""tests/tools/test_manage_workitem_stage.py
Tests for tools/manage_workitem_stage.py.
"""

from __future__ import annotations

import argparse
import re
from collections.abc import Callable
from pathlib import Path

import git
import git.exc
import pytest

from tools.manage_workitem_stage import (
    BatchResolutionError,
    _batch_prefix,
    _discover_batch,
    build_parser,
    cmd_close_batch,
    cmd_close_implementation,
    cmd_close_issue,
    cmd_close_plan,
    cmd_set_status,
    cmd_set_step_status,
    move_to_done,
    parse_execution_status_table,
)
from tools.manage_workitem_stage import _find_remote_conflict as find_remote_conflict
from tools.manage_workitem_stage import _run_with_lock_retry as run_with_lock_retry

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

# `move_to_done()`'s `kind` label for each subcommand's auto-commit message.
SUBCOMMAND_TO_KIND = {"close-issue": "issue", "close-plan": "plan"}


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
# close-issue / close-plan: uncommitted-changes auto-commit
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
def test_simple_move_autocommits_uncommitted_source(
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
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()

    # The uncommitted change was auto-committed (with the kind-labeled message)
    # before the move — the rename itself lands staged-but-uncommitted, same as
    # test_simple_move_success's already-clean case.
    kind = SUBCOMMAND_TO_KIND[subcommand]
    auto_commit_subject = repo.git.log("-1", "--format=%s")
    assert auto_commit_subject == (
        f"chore: auto-commit {kind} before archival move (20260107_dirty.md)"
    )
    status = repo.git.status("--porcelain")
    assert "R  " in status

    captured = capsys.readouterr()
    assert str(destination) in captured.out


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
@pytest.mark.parametrize(
    ("change_kind", "make_dirty"), UNCOMMITTED_CASES, ids=UNCOMMITTED_IDS
)
def test_stage_only_moves_without_creating_a_commit(
    temp_git_repo: Path,
    change_kind: str,
    make_dirty: Callable[[git.Repo, Path], None],
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / stage_dir / "20260107_dirty.md"
    make_dirty(repo, source)
    head_before = repo.head.commit.hexsha

    args = build_parser().parse_args([subcommand, str(source), "--stage-only"])
    exit_code = cmd_func(args)

    destination = temp_git_repo / stage_dir / "done" / "20260107_dirty.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()
    assert repo.head.commit.hexsha == head_before
    assert destination.read_text(encoding="utf-8").endswith("content\n")
    assert str(destination.relative_to(temp_git_repo)) in repo.git.diff(
        "--cached", "--name-only"
    )


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


@pytest.mark.parametrize(
    ("subcommand", "stage_dir", "cmd_func"), SIMPLE_MOVE_CASES, ids=SIMPLE_MOVE_IDS
)
def test_auto_commit_does_not_sweep_other_staged_changes(
    temp_git_repo: Path,
    subcommand: str,
    stage_dir: str,
    cmd_func: Callable[[argparse.Namespace], int],
) -> None:
    """The auto-commit that precedes an archival move must contain only the source file.

    `move_to_done()` stages the source with `git add <path>`, but a plain
    `git commit -m` commits whatever the caller had *already* staged too. That swept
    five unrelated `issues/done/` deletions into one `chore:` auto-commit during the
    MCP-006 run. The commit is now pathspec-limited to the source, so pre-staged
    unrelated work stays staged and out of the auto-commit.
    """
    repo = git.Repo(temp_git_repo)
    source = temp_git_repo / stage_dir / "20260110_dirty.md"
    _dirty_staged(repo, source)

    unrelated = temp_git_repo / stage_dir / "20260110_unrelated.md"
    unrelated.parent.mkdir(parents=True, exist_ok=True)
    unrelated.write_text("staged unrelated work\n", encoding="utf-8")
    repo.index.add([str(unrelated)])

    args = build_parser().parse_args([subcommand, str(source)])
    exit_code = cmd_func(args)

    destination = temp_git_repo / stage_dir / "done" / "20260110_dirty.md"
    assert exit_code == 0
    assert not source.exists()
    assert destination.exists()

    committed = repo.git.show("--name-only", "--format=", "HEAD").splitlines()
    assert committed == [f"{stage_dir}/20260110_dirty.md"]
    staged_after = repo.git.diff("--cached", "--name-only").splitlines()
    assert f"{stage_dir}/20260110_unrelated.md" in staged_after


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


# ---------------------------------------------------------------------------
# set-status / set-step-status: Execution Status table mutation.
#
# test_set_step_status_preserves_header_row is a regression test for a bug
# found while adding --started/--completed: update_execution_status()'s
# table-rebuild loop classified the header row itself as a data row (same
# cell count as the header) before the separator row had been seen, so it was
# silently dropped from the rewritten file on every set-status/set-step-status
# call.
# ---------------------------------------------------------------------------

EXECUTION_STATUS_TWO_ROWS = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | First step | Pending | — | — | |
| 2 | Second step | Pending | — | — | |
"""


def test_set_step_status_preserves_header_row(tmp_path: Path) -> None:
    source = tmp_path / "impl.md"
    source.write_text(EXECUTION_STATUS_TWO_ROWS, encoding="utf-8")

    args = build_parser().parse_args(
        [
            "set-step-status",
            "implementation-procedure",
            str(source),
            "--step",
            "1",
            "In Progress",
        ]
    )
    exit_code = cmd_set_step_status(args)

    assert exit_code == 0
    _, header, rows = parse_execution_status_table(source.read_text(encoding="utf-8"))
    assert header == ["Step", "Description", "Status", "Started", "Completed", "Notes"]
    assert rows is not None and len(rows) == 2
    assert rows[0][2] == "In Progress"
    assert rows[1][2] == "Pending"  # untouched row unaffected


def test_set_step_status_sets_started_and_completed(tmp_path: Path) -> None:
    source = tmp_path / "impl.md"
    source.write_text(EXECUTION_STATUS_TWO_ROWS, encoding="utf-8")

    args = build_parser().parse_args(
        [
            "set-step-status",
            "implementation-procedure",
            str(source),
            "--step",
            "1",
            "Completed",
            "--started",
            "20260913-090000",
            "--completed",
            "20260913-091500",
        ]
    )
    exit_code = cmd_set_step_status(args)

    assert exit_code == 0
    _, header, rows = parse_execution_status_table(source.read_text(encoding="utf-8"))
    assert header is not None and rows is not None
    row = rows[0]
    assert row[header.index("Started")] == "20260913-090000"
    assert row[header.index("Completed")] == "20260913-091500"
    # the untouched row keeps its original placeholder value
    assert rows[1][header.index("Started")] == "—"


def test_set_step_status_by_description_match(tmp_path: Path) -> None:
    source = tmp_path / "impl.md"
    source.write_text(EXECUTION_STATUS_TWO_ROWS, encoding="utf-8")

    args = build_parser().parse_args(
        [
            "set-step-status",
            "implementation-procedure",
            str(source),
            "--description",
            "Second",
            "Blocked",
            "--notes",
            "waiting on review",
        ]
    )
    exit_code = cmd_set_step_status(args)

    assert exit_code == 0
    _, header, rows = parse_execution_status_table(source.read_text(encoding="utf-8"))
    assert header is not None and rows is not None
    assert rows[0][header.index("Status")] == "Pending"  # first row untouched
    assert rows[1][header.index("Status")] == "Blocked"
    assert rows[1][header.index("Notes")] == "waiting on review"


def test_set_status_updates_all_rows_and_preserves_header(tmp_path: Path) -> None:
    source = tmp_path / "impl.md"
    source.write_text(EXECUTION_STATUS_TWO_ROWS, encoding="utf-8")

    args = build_parser().parse_args(
        [
            "set-status",
            "implementation-procedure",
            str(source),
            "Completed",
            "--completed",
            "20260913-100000",
        ]
    )
    exit_code = cmd_set_status(args)

    assert exit_code == 0
    _, header, rows = parse_execution_status_table(source.read_text(encoding="utf-8"))
    assert header == ["Step", "Description", "Status", "Started", "Completed", "Notes"]
    assert rows is not None and len(rows) == 2
    assert all(row[header.index("Status")] == "Completed" for row in rows)
    assert all(row[header.index("Completed")] == "20260913-100000" for row in rows)


def test_set_step_status_missing_step_errors(tmp_path: Path) -> None:
    source = tmp_path / "impl.md"
    source.write_text(EXECUTION_STATUS_TWO_ROWS, encoding="utf-8")

    args = build_parser().parse_args(
        [
            "set-step-status",
            "implementation-procedure",
            str(source),
            "--step",
            "99",
            "Completed",
        ]
    )
    exit_code = cmd_set_step_status(args)

    assert exit_code == 1


# Regression test for a bug found while updating
# implementations/*_scripts_eventbus_app_py.md's Execution Status table:
# update_execution_status()'s table-rebuild loop appended the rebuilt data
# rows unconditionally after the *entire file's* line loop finished, instead
# of at the point where the original data rows ended. EXECUTION_STATUS_TWO_ROWS
# above has nothing after the table, so it never exercised this path — the
# bug only shows up when a later section (e.g. "### Blocker Log") follows the
# Execution Status table, which every real implementation-procedure/plan
# document has.
EXECUTION_STATUS_WITH_TRAILING_SECTION = """# Fixture implementation procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | First step | Pending | — | — | |
| 2 | Second step | Pending | — | — | |
| 3 | Third step | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |
"""


def test_set_step_status_keeps_rows_inside_table_with_trailing_section(
    tmp_path: Path,
) -> None:
    source = tmp_path / "impl.md"
    source.write_text(EXECUTION_STATUS_WITH_TRAILING_SECTION, encoding="utf-8")

    args = build_parser().parse_args(
        [
            "set-step-status",
            "implementation-procedure",
            str(source),
            "--step",
            "1",
            "Completed",
        ]
    )
    exit_code = cmd_set_step_status(args)

    assert exit_code == 0
    written = source.read_text(encoding="utf-8")
    _, header, rows = parse_execution_status_table(written)
    assert header is not None
    assert rows is not None and len(rows) == 3
    assert rows[0][header.index("Status")] == "Completed"
    # The Blocker Log table must still be present and untouched, and the
    # rebuilt Execution Status rows must sit *before* it, not after.
    assert "### Blocker Log" in written
    execution_pos = written.index("### Execution Status")
    blocker_pos = written.index("### Blocker Log")
    row3_pos = written.index("Third step")
    assert execution_pos < row3_pos < blocker_pos

    # A subsequent update to a later step must still find its row — this is
    # what failed before the fix (Step 2/3 rows were pushed past EOF).
    args2 = build_parser().parse_args(
        [
            "set-step-status",
            "implementation-procedure",
            str(source),
            "--step",
            "2",
            "Completed",
        ]
    )
    assert cmd_set_step_status(args2) == 0


# ---------------------------------------------------------------------------
# close-issue: non-Frozen Plan block
# ---------------------------------------------------------------------------

_ISSUE_NAME = "20260101_gate.md"


def _plan_text(freeze: str | None, source: str = f"issues/{_ISSUE_NAME}") -> str:
    freeze_line = f"**Freeze status**: {freeze}\n" if freeze else ""
    return f"# Plan\n\n## Traceability\n- **Source issue**: {source}\n\n{freeze_line}"


def _setup_issue_with_plan(
    root: Path,
    freeze: str | None,
    *,
    plan_dir: str = "plans",
    source: str | None = None,
) -> Path:
    repo = git.Repo(root)
    issue = root / "issues" / _ISSUE_NAME
    _commit_file(repo, issue, "# Issue\n")
    text = _plan_text(freeze) if source is None else _plan_text(freeze, source)
    _commit_file(repo, root / plan_dir / "20260101_plan.md", text)
    return issue


@pytest.mark.parametrize("freeze", ["Draft", "Draft (was blocked)", None])
def test_close_issue_blocked_by_non_frozen_plan(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str], freeze: str | None
) -> None:
    issue = _setup_issue_with_plan(temp_git_repo, freeze)

    args = build_parser().parse_args(["close-issue", str(issue)])
    assert cmd_close_issue(args) == 1

    assert issue.exists()
    assert not (temp_git_repo / "issues" / "done" / _ISSUE_NAME).exists()
    assert "non-Frozen" in capsys.readouterr().err


def test_close_issue_allowed_when_plan_frozen(temp_git_repo: Path) -> None:
    issue = _setup_issue_with_plan(temp_git_repo, "Frozen (verified)")

    args = build_parser().parse_args(["close-issue", str(issue)])
    assert cmd_close_issue(args) == 0
    assert (temp_git_repo / "issues" / "done" / _ISSUE_NAME).exists()


def test_close_issue_ignores_draft_plan_in_plans_done(temp_git_repo: Path) -> None:
    issue = _setup_issue_with_plan(temp_git_repo, "Draft", plan_dir="plans/done")

    args = build_parser().parse_args(["close-issue", str(issue)])
    assert cmd_close_issue(args) == 0


def test_close_issue_ignores_plan_for_other_issue(temp_git_repo: Path) -> None:
    issue = _setup_issue_with_plan(
        temp_git_repo, "Draft", source="issues/20260101_other.md"
    )

    args = build_parser().parse_args(["close-issue", str(issue)])
    assert cmd_close_issue(args) == 0


def test_close_issue_force_with_reason_overrides_block(
    temp_git_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    issue = _setup_issue_with_plan(temp_git_repo, "Draft")

    args = build_parser().parse_args(
        ["close-issue", str(issue), "--force", "--reason", "plan abandoned"]
    )
    assert cmd_close_issue(args) == 0
    assert (temp_git_repo / "issues" / "done" / _ISSUE_NAME).exists()
    assert "plan abandoned" in capsys.readouterr().out


def test_close_issue_force_without_reason_errors(temp_git_repo: Path) -> None:
    issue = _setup_issue_with_plan(temp_git_repo, "Draft")

    args = build_parser().parse_args(["close-issue", str(issue), "--force"])
    assert cmd_close_issue(args) == 1
    assert issue.exists()


# ---------------------------------------------------------------------------
# close-batch: batch archival (REQ-001, REQ-002, REQ-003, REQ-004, REQ-005,
# REQ-007)
#
# close-batch discovers its batch relative to the CWD (via _impl_root()) and
# scans plans/ from the CWD, so every case below chdirs into the temp_git_repo
# first. move_to_done() resolves the repository from the source file's parent,
# so the archival move still works once the CWD is inside the temp repo.
# ---------------------------------------------------------------------------

# A clean, multi-row Execution Status table (no Pending row).
EXECUTION_STATUS_BATCH_CLEAN = """# Batch procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | First step | Completed | 20260101-000000 | 20260101-000100 | |
| 2 | Second step | In Progress | 20260101-000100 | — | |
"""

# Same shape, but the second row is Pending — enough to trip the atomic
# Pending pre-check across the whole batch.
EXECUTION_STATUS_BATCH_PENDING = """# Batch procedure

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | First step | Completed | 20260101-000000 | 20260101-000100 | |
| 2 | Second step | Pending | — | — | |
"""


@pytest.fixture
def in_temp_repo(monkeypatch: pytest.MonkeyPatch, temp_git_repo: Path) -> Path:
    """chdir into the temp repo so close-batch's CWD-relative discovery and
    owning-plan scan resolve inside the throwaway repository."""
    monkeypatch.chdir(temp_git_repo)
    return temp_git_repo


def _batch_plan_text(prefix: str = "20260101") -> str:
    """An owning plan: an Execution Status table plus an Implementation Target
    Files table that references ``implementations/<prefix>_`` so close-batch's
    content-based owning-plan lookup finds it. Named ``<prefix>_plan.md`` so the
    plan-path discovery form derives the same prefix."""
    return f"""# Batch plan

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Plan the batch | In Progress | — | — | |

## Implementation Target Files

- `implementations/{prefix}_01_proc.md`
- `implementations/{prefix}_02_proc.md`
"""


def _commit_procedure(
    repo: git.Repo, root: Path, prefix: str, index: int, status_text: str
) -> Path:
    path = root / "implementations" / f"{prefix}_{index}_proc.md"
    _commit_file(repo, path, status_text)
    return path


def _done_dir(root: Path) -> Path:
    return root / "implementations" / "done"


# ---------------------------------------------------------------------------
# close-batch: discovery (REQ-001)
# ---------------------------------------------------------------------------


def test_close_batch_discovery_from_plan_path(in_temp_repo: Path) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_procedure(repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_file(
        repo, in_temp_repo / "plans" / f"{prefix}_plan.md", _batch_plan_text(prefix)
    )

    batch_id = str(in_temp_repo / "plans" / f"{prefix}_plan.md")
    resolved = _batch_prefix(batch_id)
    files = _discover_batch(batch_id, resolved)

    # The prefix is derived from the plan filename stem, not its table.
    assert resolved == prefix
    assert [p.name for p in files] == sorted(f"{prefix}_{i}_proc.md" for i in (1, 2))


def test_close_batch_discovery_from_bare_prefix(in_temp_repo: Path) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    _commit_procedure(repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_CLEAN)

    files = _discover_batch(prefix, _batch_prefix(prefix))

    assert [p.name for p in files] == sorted(f"{prefix}_{i}_proc.md" for i in (1, 2))


def test_close_batch_unknown_batch_raises(in_temp_repo: Path) -> None:
    # A prefix with no matching procedures resolves to an error, not a silent
    # no-op — the caller turns this into an exit 1.
    with pytest.raises(BatchResolutionError):
        _discover_batch("20269999_nothing", "20269999_nothing")


# ---------------------------------------------------------------------------
# close-batch: atomic Pending refusal (REQ-002)
# ---------------------------------------------------------------------------


def test_close_batch_pending_row_refuses_and_moves_nothing(
    in_temp_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    _commit_procedure(repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_PENDING)
    plan_path = in_temp_repo / "plans" / f"{prefix}_plan.md"
    _commit_file(repo, plan_path, _batch_plan_text(prefix))
    plan_before = plan_path.read_text(encoding="utf-8")

    args = build_parser().parse_args(["close-batch", prefix])
    exit_code = cmd_close_batch(args)

    assert exit_code == 1
    # No file moved: both procedures still present, nothing staged into done/.
    assert (in_temp_repo / "implementations" / f"{prefix}_1_proc.md").exists()
    assert (in_temp_repo / "implementations" / f"{prefix}_2_proc.md").exists()
    assert list(_done_dir(in_temp_repo).glob("*")) == []
    # The plan was not touched.
    assert plan_path.read_text(encoding="utf-8") == plan_before
    assert "Pending" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# close-batch: idempotency (REQ-007)
# ---------------------------------------------------------------------------


def test_close_batch_idempotent_second_run_is_noop(
    in_temp_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    _commit_procedure(repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_file(
        repo, in_temp_repo / "plans" / f"{prefix}_plan.md", _batch_plan_text(prefix)
    )

    assert cmd_close_batch(build_parser().parse_args(["close-batch", prefix])) == 0
    done = _done_dir(in_temp_repo)
    assert (done / f"{prefix}_1_proc.md").exists()
    assert (done / f"{prefix}_2_proc.md").exists()

    # Second run on the same batch id is a no-op, not a partial re-run, and
    # raises no error.
    assert cmd_close_batch(build_parser().parse_args(["close-batch", prefix])) == 0
    captured = capsys.readouterr()
    assert "already closed" in captured.out.lower()
    # Still exactly the two archived files; nothing duplicated or missing.
    assert sorted(p.name for p in done.glob(f"{prefix}_*.md")) == sorted(
        f"{prefix}_{i}_proc.md" for i in (1, 2)
    )


# ---------------------------------------------------------------------------
# close-batch: dry-run (REQ-005)
# ---------------------------------------------------------------------------


def test_close_batch_dry_run_changes_nothing(
    in_temp_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    proc1 = _commit_procedure(
        repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN
    )
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_CLEAN)
    plan_path = in_temp_repo / "plans" / f"{prefix}_plan.md"
    _commit_file(repo, plan_path, _batch_plan_text(prefix))
    plan_before = plan_path.read_text(encoding="utf-8")

    args = build_parser().parse_args(["close-batch", prefix, "--dry-run"])
    exit_code = cmd_close_batch(args)

    assert exit_code == 0
    # Nothing moved, plan untouched.
    assert proc1.exists()
    assert (in_temp_repo / "implementations" / f"{prefix}_2_proc.md").exists()
    assert not list(_done_dir(in_temp_repo).glob("*"))
    assert plan_path.read_text(encoding="utf-8") == plan_before
    # Output lists every planned move and edit.
    captured = capsys.readouterr()
    assert f"move {proc1.relative_to(in_temp_repo)} ->" in captured.out
    assert "edit" in captured.out


def test_close_batch_dry_run_pending_reports_block(
    in_temp_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    _commit_procedure(repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_PENDING)

    # The atomic pre-check runs even in --dry-run: a Pending row blocks before any
    # planned-move listing, so the output reports the block rather than a clean plan.
    args = build_parser().parse_args(["close-batch", prefix, "--dry-run"])
    assert cmd_close_batch(args) == 1
    captured = capsys.readouterr()
    assert "Pending" in captured.err
    assert "dry-run" not in captured.out.lower()


# ---------------------------------------------------------------------------
# close-batch: temp-git integration (REQ-003, REQ-004)
# ---------------------------------------------------------------------------


def test_close_batch_integration_archives_and_updates_plan(
    in_temp_repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = git.Repo(in_temp_repo)
    prefix = "20260101"
    _commit_procedure(repo, in_temp_repo, prefix, 1, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_procedure(repo, in_temp_repo, prefix, 2, EXECUTION_STATUS_BATCH_CLEAN)
    _commit_file(
        repo, in_temp_repo / "plans" / f"{prefix}_plan.md", _batch_plan_text(prefix)
    )

    exit_code = cmd_close_batch(build_parser().parse_args(["close-batch", prefix]))

    assert exit_code == 0
    # Both procedures moved into implementations/done/.
    done = _done_dir(in_temp_repo)
    assert not (in_temp_repo / "implementations" / f"{prefix}_1_proc.md").exists()
    assert not (in_temp_repo / "implementations" / f"{prefix}_2_proc.md").exists()
    assert (done / f"{prefix}_1_proc.md").exists()
    assert (done / f"{prefix}_2_proc.md").exists()

    # The owning plan's Execution Status rows are now Completed with
    # YYYYMMDD-HHMMSS timestamps.
    _, header, rows = parse_execution_status_table(
        (in_temp_repo / "plans" / f"{prefix}_plan.md").read_text(encoding="utf-8")
    )
    assert header is not None and rows is not None
    status_col = header.index("Status")
    started_col = header.index("Started")
    completed_col = header.index("Completed")
    assert all(row[status_col] == "Completed" for row in rows)
    for row in rows:
        assert re.fullmatch(r"\d{8}-\d{6}", row[started_col])
        assert re.fullmatch(r"\d{8}-\d{6}", row[completed_col])
