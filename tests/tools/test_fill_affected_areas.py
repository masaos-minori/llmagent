"""tests/tools/test_fill_affected_areas.py
Unit tests for tools/fill_affected_areas.py on temporary git repositories.
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import tools.fill_affected_areas as fa

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git is required")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DEPLOY_SH = (
    "#!/bin/bash\n"
    'rsync -av --delete "${REPO_ROOT}/scripts/" "${DEPLOY_SCRIPTS}/"\n'
    'cp "${REPO_ROOT}/config/agent.toml"   "${DEPLOY_CONFIG}/"\n'
)

_TARGET_HEADER = (
    "| File Path | Change Responsibility | Reason for Modification | "
    "Related Requirement / Acceptance Criterion | Repository Evidence | "
    "Related Tests | Validation Status |\n"
    "|---|---|---|---|---|---|---|\n"
)
_AFFECTED_HEADER = (
    "| File | Change | Blast Radius | Churn (30d) | Bus Factor | "
    "deploy.sh Impact |\n|---|---|---|---|---|---|\n"
)


def _git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    merged = {**os.environ, **(env or {})}
    subprocess.run(
        ["git", "-C", str(repo), "-c", "commit.gpgsign=false", *args],
        check=True,
        capture_output=True,
        stdin=subprocess.DEVNULL,
        env=merged,
    )


def _commit(repo: Path, rel: str, author: str, days_ago: int) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"{author} {days_ago}\n")
    when = (datetime.now() - timedelta(days=days_ago)).isoformat()
    env = {
        "GIT_AUTHOR_NAME": author,
        "GIT_AUTHOR_EMAIL": f"{author.lower()}@example.invalid",
        "GIT_COMMITTER_NAME": author,
        "GIT_COMMITTER_EMAIL": f"{author.lower()}@example.invalid",
        "GIT_AUTHOR_DATE": when,
        "GIT_COMMITTER_DATE": when,
    }
    _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", f"change {rel}", env=env)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "master")
    (root / "deploy").mkdir()
    (root / "deploy" / "deploy.sh").write_text(DEPLOY_SH, encoding="utf-8")
    return root


def _plan(root: Path, rows: list[tuple[str, str]], affected: str = "") -> Path:
    targets = "".join(
        f"| `{path}` | {resp} | r | REQ-001 | e | t | Verified |\n"
        for path, resp in rows
    )
    text = (
        "## Goal\n- keep this line\n\n"
        "## Implementation Target Files\n**Freeze status**: Frozen\n\n"
        f"{_TARGET_HEADER}{targets}\n"
        "## Affected areas\nintro\n\n"
        f"{_AFFECTED_HEADER}{affected or '| | | | | | |\n'}\n"
        "## Design\nkeep design\n"
    )
    plan = root / "plan.md"
    plan.write_text(text, encoding="utf-8")
    return plan


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Create the tool", "Create"),
        ("New file", "Create"),
        ("generated block", "Create"),
        ("Delete the module", "Delete"),
        ("remove the shim", "Delete"),
        ("Edit the parser", "Modify"),
        ("create and remove", "Create"),
    ],
)
def test_change_kind(text: str, expected: str) -> None:
    assert fa.change_kind(text) == expected


def test_churn_counts_only_commits_inside_window(repo: Path) -> None:
    # Dates must be monotonic: `git log --since` stops at the first older commit.
    _commit(repo, "a.py", "Alice", 60)
    _commit(repo, "a.py", "Alice", 5)
    assert fa.churn(repo, "a.py", "30.days") == 1


@pytest.mark.parametrize(
    ("names", "expected"),
    [
        (["Alice", "alice"], "High (100% single author)"),
        (["a"] * 7 + ["b"] * 3, "Low (70% top author)"),
        (["a"] * 3 + ["b"], "High (75% single author)"),
        (["a", "b"], "Low (50% top author)"),
        ([], "N/A: no history"),
    ],
)
def test_bus_factor(names: list[str], expected: str) -> None:
    assert fa.bus_factor(names) == expected


def test_new_deleted_and_history_less_files(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _commit(repo, "old.py", "Alice", 3)
    plan = _plan(
        repo,
        [
            ("new.py", "Create the file"),
            ("old.py", "Delete the file"),
            ("untracked.py", "Edit it"),
        ],
    )
    (repo / "untracked.py").write_text("x\n", encoding="utf-8")
    assert fa.main([str(plan), "--root", str(repo)]) == 0
    rows = capsys.readouterr().out.splitlines()
    assert (
        "| `new.py` | Create | TODO: author judgment | N/A (new) | N/A (new) |"
        in rows[0]
    )
    assert (
        "| Delete | TODO: author judgment | 1 | High (100% single author) |" in rows[1]
    )
    assert "N/A: no history | N/A: no history |" in rows[2]


def test_deploy_impact_mapping() -> None:
    sh = DEPLOY_SH
    for path in ("scripts/x.py", "tests/x.py", "docs/x.md", "registry/x.json"):
        assert fa.deploy_impact(path, "Modify", sh) == "not applicable (rsynced)"
    for path in ("tools/x.py", "skills/x.md", "rules/x.md"):
        assert fa.deploy_impact(path, "Modify", sh) == "not applicable (not rsynced)"
    assert fa.deploy_impact("config/n.toml", "Create", sh) == "add cp line"
    assert fa.deploy_impact("config/n.toml", "Delete", sh) == "remove cp line"
    assert fa.deploy_impact("config/agent.toml", "Modify", sh) == (
        "existing cp line at deploy/deploy.sh:3; no change needed"
    )
    assert fa.deploy_impact("config/other.toml", "Modify", sh) == (
        "Needs review: no cp line"
    )


def test_live_deploy_script_keeps_the_rsync_lines_the_mapping_relies_on() -> None:
    text = (REPO_ROOT / "deploy" / "deploy.sh").read_text(encoding="utf-8")
    for directory in fa.RSYNCED_DIRS:
        assert f'"${{REPO_ROOT}}/{directory}"' in text, directory


def test_size_note(repo: Path) -> None:
    (repo / "scripts").mkdir()
    (repo / "scripts" / "m.py").write_bytes(b"x" * 100)
    assert fa.size_note(repo, "scripts/m.py") == "scripts/m.py: 100 B, headroom 24476 B"
    assert fa.size_note(repo, "scripts/new.py") == (
        "scripts/new.py: new file, limit 24576 B"
    )
    assert fa.size_note(repo, "tools/x.py") is None


def test_default_run_is_read_only(repo: Path) -> None:
    _commit(repo, "a.py", "Alice", 2)
    plan = _plan(repo, [("a.py", "Edit")])
    before = plan.read_bytes()
    assert fa.main([str(plan), "--root", str(repo)]) == 0
    assert plan.read_bytes() == before


def test_insert_changes_only_affected_areas(repo: Path) -> None:
    _commit(repo, "a.py", "Alice", 2)
    _commit(repo, "b.py", "Bob", 2)
    keep = "| `a.py` | Modify | Medium — my judgment | 9 | stale | stale |\n"
    plan = _plan(repo, [("a.py", "Edit"), ("b.py", "Edit")], affected=keep)
    before = plan.read_text(encoding="utf-8")
    assert fa.main([str(plan), "--root", str(repo), "--insert"]) == 0
    after = plan.read_text(encoding="utf-8")
    assert "Medium — my judgment | 1 | High (100% single author)" in after
    assert "| `b.py` | Modify | TODO: author judgment | 1 |" in after
    assert "| 9 |" not in after
    head_before, _, tail_before = before.partition("## Affected areas")
    head_after, _, tail_after = after.partition("## Affected areas")
    assert head_before == head_after
    assert tail_before.split("## Design")[1] == tail_after.split("## Design")[1]


def test_insert_dry_run_writes_nothing(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _commit(repo, "a.py", "Alice", 2)
    plan = _plan(repo, [("a.py", "Edit")])
    before = plan.read_bytes()
    assert fa.main([str(plan), "--root", str(repo), "--insert", "--dry-run"]) == 0
    assert plan.read_bytes() == before
    assert "TODO: author judgment" in capsys.readouterr().out


def test_output_is_the_same_with_a_never_written_stdin(
    repo: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _commit(repo, "a.py", "Alice", 2)
    plan = _plan(repo, [("a.py", "Edit")])
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    assert fa.main([str(plan), "--root", str(repo)]) == 0
    closed = capsys.readouterr().out
    read_fd, write_fd = os.pipe()
    try:
        with os.fdopen(read_fd) as blocking:
            monkeypatch.setattr("sys.stdin", blocking)
            assert fa.main([str(plan), "--root", str(repo)]) == 0
    finally:
        os.close(write_fd)
    assert capsys.readouterr().out == closed


def test_missing_targets_and_missing_plan(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert fa.main([str(repo / "absent.md")]) == 2
    empty = repo / "empty.md"
    empty.write_text(
        "## Implementation Target Files\n\n" + _TARGET_HEADER + "| | | | | | | |\n",
        encoding="utf-8",
    )
    assert fa.main([str(empty), "--root", str(repo)]) == 1
    assert "no target rows" in capsys.readouterr().err
