"""tests/tools/test_coverage_xml_changed.py
Unit tests for tools/coverage_xml_changed.py in temporary git repositories.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import tools.coverage_xml_changed as cxc


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q", "-b", "master")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "t")
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "a.py").write_text("a = 1\n")
    (tmp_path / "scripts" / "gone.py").write_text("g = 1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-q", "-m", "base")
    _git(tmp_path, "checkout", "-q", "-b", "feature")
    return tmp_path


def test_no_changes_returns_empty(repo: Path) -> None:
    assert cxc.changed_source_files("master", cwd=repo) == []


def test_collects_committed_unstaged_and_untracked(repo: Path) -> None:
    (repo / "scripts" / "b.py").write_text("b = 1\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "add b")
    (repo / "scripts" / "a.py").write_text("a = 2\n")
    (repo / "scripts" / "c.py").write_text("c = 1\n")
    (repo / "README.md").write_text("x\n")
    assert cxc.changed_source_files("master", cwd=repo) == [
        "scripts/a.py",
        "scripts/b.py",
        "scripts/c.py",
    ]


def test_deleted_file_is_excluded(repo: Path) -> None:
    (repo / "scripts" / "gone.py").unlink()
    assert cxc.changed_source_files("master", cwd=repo) == []


def test_unknown_base_raises(repo: Path) -> None:
    with pytest.raises(RuntimeError):
        cxc.changed_source_files("no-such-branch", cwd=repo)


def test_build_command_include_and_full() -> None:
    assert cxc.build_command(["scripts/a.py", "scripts/b.py"])[-1] == (
        "--include=scripts/a.py,scripts/b.py"
    )
    assert not any(a.startswith("--include") for a in cxc.build_command([]))


def test_main_dry_run_and_error(
    repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    original = cxc.changed_source_files
    monkeypatch.setattr(cxc, "REPO_ROOT", repo)
    monkeypatch.setattr(
        cxc, "changed_source_files", lambda base: original(base, cwd=repo)
    )
    (repo / "scripts" / "a.py").write_text("a = 2\n")
    assert cxc.main(["--dry-run"]) == 0
    assert "--include=scripts/a.py" in capsys.readouterr().out
    assert cxc.main(["--base", "no-such-branch"]) == 2
