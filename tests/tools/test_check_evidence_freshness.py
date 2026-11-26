"""tests/tools/test_check_evidence_freshness.py

Tests for tools/check_evidence_freshness.py on temporary git repositories: unchanged,
committed, staged, unstaged, untracked, deleted, and created-after files, `--also`
(unrecorded) paths, the derived cited-path set, a procedure resolved through its
`Source plan`, the input errors (exit 2), and `record`.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tools import check_evidence_freshness as cef

_ID = [
    "-c",
    "user.name=t",
    "-c",
    "user.email=t@example.com",
    "-c",
    "commit.gpgsign=false",
]


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *_ID, *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _commit(root: Path, message: str = "c") -> str:
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    _git(tmp_path, "init", "-q")
    _write(tmp_path, "tools/a.py", "a = 1\n")
    _write(tmp_path, "docs/b.md", "# b\n")
    _write(tmp_path, "tests/test_a.py", "def test_a(): ...\n")
    return tmp_path, _commit(tmp_path)


def _plan(
    root: Path,
    sha: str | None,
    cited: str = "`tools/a.py`, `docs/b.md:12`, `tests/test_a.py`",
) -> Path:
    revision = f"- **Evidence revision**: {sha}\n" if sha else ""
    _write(
        root,
        "plans/p.md",
        f"## Evidence\n{cited}\n\n## Traceability\n- **Generated at**: 1\n{revision}",
    )
    return root / "plans" / "p.md"


def _check(root: Path, plan: Path, *extra: str) -> int:
    return cef.main(["check", str(plan), "--root", str(root), *extra])


def test_unchanged_files_exit_zero_and_are_counted(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo

    assert _check(root, _plan(root, sha)) == 0

    assert (
        "unchanged: 3; changed: 0; uncommitted: 0; unrecorded: 0"
        in capsys.readouterr().out
    )


def test_a_later_commit_is_reported_as_changed(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    plan = _plan(root, sha)
    _write(root, "tools/a.py", "a = 2\n")
    _commit(root)

    assert _check(root, plan) == 1

    out = capsys.readouterr().out
    assert "changed: tools/a.py" in out
    assert "unchanged: 2; changed: 1" in out


def test_unstaged_and_staged_changes_are_reported_as_uncommitted(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    plan = _plan(root, sha)
    _write(root, "tools/a.py", "a = 3\n")
    _write(root, "docs/b.md", "# changed\n")
    _git(root, "add", "docs/b.md")

    assert _check(root, plan) == 1

    out = capsys.readouterr().out
    assert "uncommitted: tools/a.py" in out
    assert "uncommitted: docs/b.md" in out


def test_a_deleted_file_is_reported_committed_or_not(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    plan = _plan(root, sha)
    (root / "tools" / "a.py").unlink()
    assert _check(root, plan) == 1
    assert "uncommitted: tools/a.py" in capsys.readouterr().out

    _commit(root)

    assert _check(root, plan) == 1
    assert "changed: tools/a.py" in capsys.readouterr().out


def test_a_file_created_after_the_revision_is_reported(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    plan = _plan(root, sha, "`tools/new.py`")
    _write(root, "tools/new.py", "x = 1\n")
    assert _check(root, plan) == 1
    assert "uncommitted: tools/new.py" in capsys.readouterr().out

    _commit(root)

    assert _check(root, plan) == 1
    assert "changed: tools/new.py" in capsys.readouterr().out


def test_a_file_absent_at_the_revision_and_still_absent_is_unchanged(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo

    assert _check(root, _plan(root, sha, "`tools/will_be_created.py`")) == 0

    assert "unchanged: 1" in capsys.readouterr().out


def test_an_also_path_the_plan_does_not_cite_is_unrecorded(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    plan = _plan(root, sha)

    assert _check(root, plan, "--also", "scripts/other.py") == 1

    out = capsys.readouterr().out
    assert "unrecorded: scripts/other.py" in out
    assert "unrecorded: 1" in out


def test_an_also_path_the_plan_cites_is_classified_normally(
    repo: tuple[Path, str],
) -> None:
    root, sha = repo

    assert _check(root, _plan(root, sha), "--also", "tools/a.py") == 0


def test_only_repository_paths_are_cited() -> None:
    text = (
        "`tools/a.py:12` `tools/a.py:3-9` `tools/a.py` `tests/x.py::test_y` `plans/{filename}.md` "
        "`tools/*.py` `uv run pytest tests/x.py` `word` `a/b` `-x/y`"
    )

    assert cef.cited_paths(text) == ["tools/a.py", "a/b"]


def test_the_document_itself_is_never_cited(repo: tuple[Path, str]) -> None:
    root, sha = repo
    plan = _plan(root, sha, "`plans/p.md`, `tools/a.py`")

    assert _check(root, plan) == 0


def test_a_procedure_resolves_the_revision_through_its_source_plan(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    _plan(root, sha)
    _commit(root)
    _write(
        root,
        "implementations/i.md",
        "## Traceability\n- **Source plan**: plans/p.md\n\n`tools/a.py`\n",
    )
    assert _check(root, root / "implementations" / "i.md") == 0

    (root / "plans").rename(root / "plans_old")
    (root / "plans" / "done").mkdir(parents=True)
    (root / "plans_old" / "p.md").rename(root / "plans" / "done" / "p.md")
    capsys.readouterr()

    assert _check(root, root / "implementations" / "i.md") == 0
    assert "revision" in capsys.readouterr().out


def test_missing_revision_unknown_sha_and_unreadable_document_exit_two(
    repo: tuple[Path, str],
) -> None:
    root, sha = repo

    assert _check(root, _plan(root, None)) == 2
    assert _check(root, _plan(root, "0" * 40)) == 2
    assert _check(root, root / "plans" / "absent.md") == 2


def test_record_prints_the_head_line_when_the_cited_files_are_clean(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, sha = repo
    plan = _plan(root, None)

    assert cef.main(["record", str(plan), "--root", str(root)]) == 0

    assert capsys.readouterr().out.strip() == f"- **Evidence revision**: {sha}"


def test_record_refuses_while_a_cited_file_is_uncommitted(
    repo: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, _ = repo
    plan = _plan(root, None)
    _write(root, "tools/a.py", "a = 9\n")

    assert cef.main(["record", str(plan), "--root", str(root)]) == 1

    out = capsys.readouterr().out
    assert "uncommitted: tools/a.py" in out
    assert "Evidence revision" not in out


def test_the_tool_writes_nothing(repo: tuple[Path, str]) -> None:
    root, sha = repo
    plan = _plan(root, sha)
    before = _git(root, "status", "--porcelain")
    text = plan.read_text(encoding="utf-8")

    _check(root, plan)
    cef.main(["record", str(plan), "--root", str(root)])

    assert plan.read_text(encoding="utf-8") == text
    assert _git(root, "status", "--porcelain") == before
