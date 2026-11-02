"""tests/tools/test_classify_changes.py
Unit tests for tools/classify_changes.py over fixture porcelain bytes, plus
end-to-end tests of the documented pathspec split in temporary git repositories.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest

import tools.classify_changes as cc


def _z(*entries: str) -> bytes:
    """Build `git status --porcelain=v1 -z` bytes from already-joined entries."""
    return "".join(f"{e}\0" for e in entries).encode("utf-8")


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return proc.stdout


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q", "-b", "master")
    _git(repo, "config", "user.name", "tester")
    _git(repo, "config", "user.email", "tester@example.invalid")
    _git(repo, "config", "commit.gpgsign", "false")


def _status_file(tmp_path: Path, raw: bytes) -> Path:
    path = tmp_path / "status.bin"
    path.write_bytes(raw)
    return path


# --- parser ------------------------------------------------------------


def test_parse_modification_and_unstaged() -> None:
    changes = cc.parse_porcelain_z(_z("M  a.py", " M b.py"))
    assert [c.path for c in changes] == ["a.py", "b.py"]
    assert changes[0].is_staged and not changes[0].is_worktree_only
    assert changes[1].is_worktree_only and not changes[1].is_staged


def test_parse_rename_keeps_both_names() -> None:
    changes = cc.parse_porcelain_z(_z("R  new.md", "old.md", "M  next.py"))
    assert len(changes) == 2
    assert changes[0].path == "new.md"
    assert changes[0].orig_path == "old.md"
    assert changes[1].path == "next.py"
    assert changes[1].orig_path is None


def test_parse_untracked_deleted_and_ignored() -> None:
    changes = cc.parse_porcelain_z(_z("?? x", "D  y", " D z", "!! i"))
    assert [c.path for c in changes] == ["x", "y", "z"]
    assert changes[0].is_untracked
    assert changes[1].is_staged
    assert changes[2].is_worktree_only


@pytest.mark.parametrize("raw", [b"M\0", b"MM\0", b"MMx path\0"])
def test_parse_rejects_short_entry(raw: bytes) -> None:
    with pytest.raises(ValueError):
        cc.parse_porcelain_z(raw)


def test_parse_rejects_rename_without_original() -> None:
    with pytest.raises(ValueError):
        cc.parse_porcelain_z(_z("R  new.md"))


def test_parse_unusual_names() -> None:
    names = ["with space.py", "it's.py", "naïve_名前.py"]
    changes = cc.parse_porcelain_z(_z(*[f"M  {n}" for n in names]))
    assert [c.path for c in changes] == names
    rendered = cc.render(cc.classify(changes))
    spec_line = next(x for x in rendered.splitlines() if x.startswith("pathspec:"))
    assert shlex.split(spec_line.removeprefix("pathspec:")) == names


# --- classification ----------------------------------------------------


def test_classify_groups() -> None:
    paths = {
        "plans/done/p.md": "artifacts",
        "issues/i.md": "artifacts",
        "implementations/done/x.md": "artifacts",
        "scripts/agent/a.py": "code",
        "config/agent.toml": "code",
        "deploy/run.sh": "code",
        "tests/tools/x.py": "tests",
        "tools/t.py": "tools",
        "docs/d.md": "docs",
        "skills/s/SKILL.md": "docs",
        "rules/r.md": "docs",
        "templates/t.md": "docs",
        "prompts/p.md": "docs",
        "routing.md": "docs",
        "AGENTS.md": "docs",
        "CLAUDE.md": "docs",
        "pyproject.toml": "other",
    }
    for path, expected in paths.items():
        assert cc.group_of(path) == expected, path
    result = cc.classify(cc.parse_porcelain_z(_z(*[f"M  {p}" for p in paths])))
    for group in cc.GROUP_ORDER:
        assert result.pathspec[group], group


def test_rename_pair_stays_in_one_group() -> None:
    changes = cc.parse_porcelain_z(_z("R  plans/done/x.md", "plans/x.md"))
    result = cc.classify(changes)
    assert result.pathspec["artifacts"] == ["plans/done/x.md", "plans/x.md"]
    assert result.warnings == []


def test_cross_group_rename_noted() -> None:
    changes = cc.parse_porcelain_z(_z("R  tools/a.py", "scripts/a.py"))
    result = cc.classify(changes)
    assert result.pathspec["tools"] == ["tools/a.py", "scripts/a.py"]
    assert result.pathspec["code"] == []
    assert result.warnings == [
        "NOTE cross-group-rename: scripts/a.py -> tools/a.py (grouped under tools/a.py)"
    ]
    assert not result.blocking


def test_untracked_and_unstaged_not_in_pathspec() -> None:
    changes = cc.parse_porcelain_z(
        _z("M  tools/a.py", " M tools/b.py", "?? tools/c.py")
    )
    result = cc.classify(changes)
    assert result.pathspec["tools"] == ["tools/a.py"]
    assert result.unstaged["tools"] == ["tools/b.py"]
    assert result.untracked["tools"] == ["tools/c.py"]
    rendered = cc.render(result)
    assert "unstaged: tools/b.py" in rendered
    assert "untracked: tools/c.py" in rendered
    assert "pathspec: tools/a.py" in rendered


def test_deleted_path_is_staged_when_index_column_set() -> None:
    result = cc.classify(
        cc.parse_porcelain_z(_z("D  tools/gone.py", " D tools/lost.py"))
    )
    assert result.pathspec["tools"] == ["tools/gone.py"]
    assert result.unstaged["tools"] == ["tools/lost.py"]


def test_partly_staged_flagged_and_exit_1(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    raw = _z("MM tools/a.py", "RM plans/done/x.md", "plans/x.md")
    result = cc.classify(cc.parse_porcelain_z(raw))
    assert "WARN partly-staged: tools/a.py" in result.warnings
    assert "WARN partly-staged: plans/done/x.md" in result.warnings
    assert cc.main(["--status-file", str(_status_file(tmp_path, raw))]) == 1
    assert "WARN partly-staged" in capsys.readouterr().out
    clean = _status_file(tmp_path, _z("M  tools/a.py"))
    assert cc.main(["--status-file", str(clean)]) == 0


def test_unmerged_flagged(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    status = _status_file(tmp_path, _z("UU tools/a.py", "M  tools/b.py"))
    assert cc.main(["--status-file", str(status)]) == 1
    out = capsys.readouterr().out
    assert "WARN unmerged: tools/a.py" in out
    assert "pathspec: tools/b.py" in out


# --- verify-pathspec and options ----------------------------------------


def test_verify_pathspec_refuses_half_pair(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = _status_file(tmp_path, _z("R  plans/done/x.md", "plans/x.md"))
    args = ["--status-file", str(status), "--verify-pathspec"]
    assert cc.main([*args, "plans/done/x.md"]) == 1
    assert "split-rename: plans/done/x.md needs plans/x.md" in capsys.readouterr().out
    assert cc.main([*args, "plans/x.md"]) == 1
    assert "split-rename: plans/x.md needs plans/done/x.md" in capsys.readouterr().out
    assert cc.main([*args, "plans/done/x.md", "plans/x.md"]) == 0
    assert capsys.readouterr().out == ""


def test_group_option_prints_only_that_pathspec(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = _status_file(
        tmp_path, _z("M  tools/a.py", "R  plans/done/x.md", "plans/x.md")
    )
    assert cc.main(["--status-file", str(status), "--group", "artifacts"]) == 0
    assert capsys.readouterr().out.strip() == "plans/done/x.md plans/x.md"
    assert cc.main(["--status-file", str(status), "--group", "docs"]) == 0
    assert capsys.readouterr().out == ""


def test_unknown_group_exit_2(tmp_path: Path) -> None:
    status = _status_file(tmp_path, _z("M  tools/a.py"))
    assert cc.main(["--status-file", str(status), "--group", "nope"]) == 2


def test_malformed_status_file_exit_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = _status_file(tmp_path, b"x\0")
    assert cc.main(["--status-file", str(status)]) == 2
    assert "error:" in capsys.readouterr().err


def test_missing_status_file_exit_2(tmp_path: Path) -> None:
    assert cc.main(["--status-file", str(tmp_path / "absent.bin")]) == 2


def test_status_from_stdin(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    import io
    import sys

    class _Stdin:
        buffer = io.BytesIO(_z("M  tools/a.py"))

    monkeypatch.setattr(sys, "stdin", _Stdin())
    assert cc.main(["--status-file", "-"]) == 0
    assert "pathspec: tools/a.py" in capsys.readouterr().out


# --- end-to-end in temporary repositories --------------------------------


def _split_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    (repo / "tools").mkdir()
    (repo / "plans").mkdir()
    (repo / "plans" / "done").mkdir()
    (repo / "tools" / "t.py").write_text("x = 1\n")
    (repo / "plans" / "x.md").write_text("plan\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    (repo / "tools" / "t.py").write_text("x = 2\n")
    _git(repo, "add", "tools/t.py")
    _git(repo, "mv", "plans/x.md", "plans/done/x.md")
    return repo


def _group_pathspec(
    repo: Path, group: str, monkeypatch: pytest.MonkeyPatch
) -> list[str]:
    monkeypatch.chdir(repo)
    out = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout
    result = cc.classify(cc.parse_porcelain_z(out))
    return result.pathspec[group]


def test_split_commits_two_groups(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _split_repo(tmp_path)
    tools_spec = _group_pathspec(repo, "tools", monkeypatch)
    artifacts_spec = _group_pathspec(repo, "artifacts", monkeypatch)
    assert tools_spec == ["tools/t.py"]
    assert artifacts_spec == ["plans/done/x.md", "plans/x.md"]
    base = _git(repo, "rev-parse", "HEAD").strip()

    _git(repo, "commit", "-q", "-m", "tools: change", "--", *tools_spec)
    # The staged rename stays staged after the first pathspec commit.
    assert "R  plans/x.md -> plans/done/x.md" in _git(repo, "status", "--short")
    _git(repo, "commit", "-q", "-m", "plan: archive", "--", *artifacts_spec)

    assert _git(repo, "status", "--porcelain").strip() == ""
    commits = _git(repo, "rev-list", f"{base}..HEAD").split()
    assert len(commits) == 2
    first = _git(repo, "show", "--name-only", "--format=", commits[1]).split()
    assert first == ["tools/t.py"]
    last = _git(repo, "show", "--name-status", "-M", "--format=", "HEAD").strip()
    assert last.startswith("R100")
    assert "plans/x.md" in last and "plans/done/x.md" in last


def test_commit_of_new_name_only_leaves_staged_deletion(tmp_path: Path) -> None:
    repo = _split_repo(tmp_path)
    _git(repo, "commit", "-q", "-m", "plan: half", "--", "plans/done/x.md")
    assert "D  plans/x.md" in _git(repo, "status", "--short")


def test_pathspec_commit_includes_unstaged_part_of_mm_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _split_repo(tmp_path)
    (repo / "tools" / "t.py").write_text(
        "x = 3\n"
    )  # unstaged edit on top of the staged one
    monkeypatch.chdir(repo)
    # The classifier flags the path before the commit (exit 1, partly-staged).
    assert cc.main([]) == 1
    assert "WARN partly-staged: tools/t.py" in capsys.readouterr().out
    _git(repo, "commit", "-q", "-m", "tools: change", "--", "tools/t.py")
    assert _git(repo, "show", "HEAD:tools/t.py") == "x = 3\n"


def test_main_never_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = _split_repo(tmp_path)
    (repo / "untracked.txt").write_text("u\n")
    monkeypatch.chdir(repo)

    def snapshot() -> tuple[str, str, str]:
        return (
            _git(repo, "status", "--porcelain=v1", "-z"),
            _git(repo, "ls-files", "-s"),
            (repo / "tools" / "t.py").read_text(),
        )

    before = snapshot()
    cc.main([])
    cc.main(["--group", "tools"])
    cc.main(["--verify-pathspec", "plans/done/x.md"])
    assert snapshot() == before
