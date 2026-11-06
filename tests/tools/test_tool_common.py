"""tests/tools/test_tool_common.py
Tests for tools/_tool_common.py: the shared repository root, the git runner, and the
exit-code constants.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from tools import _tool_common
from tools._tool_common import (
    EXIT_ERROR,
    EXIT_FINDINGS,
    EXIT_OK,
    REPO_ROOT,
    run_git,
)


def _init_repo(repo: Path) -> None:
    run_git("init", "-q", cwd=repo, check=True)


def test_exit_constants_follow_the_cli_convention() -> None:
    assert (EXIT_OK, EXIT_FINDINGS, EXIT_ERROR) == (0, 1, 2)


def test_repo_root_is_the_directory_above_tools() -> None:
    assert (REPO_ROOT / "tools" / "_tool_common.py").is_file()
    assert (REPO_ROOT / ".git").exists()


def test_success_returns_text_stdout(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    proc = run_git("rev-parse", "--is-inside-work-tree", cwd=tmp_path)
    assert proc.returncode == 0
    assert proc.stdout.strip() == "true"
    assert isinstance(proc.stdout, str)


def test_bytes_mode_returns_nul_delimited_output(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("b\n", encoding="utf-8")
    run_git("add", "a.txt", "b.txt", cwd=tmp_path, check=True)
    proc = run_git("ls-files", "-z", cwd=tmp_path, binary=True)
    assert isinstance(proc.stdout, bytes)
    assert proc.stdout == b"a.txt\0b.txt\0"


def test_failure_without_check_reports_returncode_and_stderr(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    proc = run_git("cat-file", "-p", "0" * 40, cwd=tmp_path)
    assert proc.returncode != 0
    assert proc.stderr.strip() != ""


def test_failure_with_check_raises_with_text_stderr(tmp_path: Path) -> None:
    _init_repo(tmp_path)
    with pytest.raises(subprocess.CalledProcessError) as excinfo:
        run_git("cat-file", "-p", "0" * 40, cwd=tmp_path, check=True)
    assert isinstance(excinfo.value.stderr, str)
    assert excinfo.value.stderr.strip() != ""


def test_non_utf8_stdout_is_replaced_in_text_mode_and_kept_in_bytes_mode(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    blob = tmp_path / "blob.bin"
    blob.write_bytes(b"ok\xff\xfe\n")
    sha = run_git(
        "hash-object", "-w", "blob.bin", cwd=tmp_path, check=True
    ).stdout.strip()

    text = run_git("cat-file", "-p", sha, cwd=tmp_path, check=True)
    assert text.stdout == "ok��\n"

    raw = run_git("cat-file", "-p", sha, cwd=tmp_path, binary=True, check=True)
    assert raw.stdout == b"ok\xff\xfe\n"


def test_non_utf8_stderr_is_replaced_in_text_mode_and_kept_in_bytes_mode(
    tmp_path: Path,
) -> None:
    _init_repo(tmp_path)
    bad_name = "\udcff"  # encodes to the single byte 0xff through surrogateescape

    text = run_git("cat-file", "-p", bad_name, cwd=tmp_path)
    assert text.returncode != 0
    assert "�" in text.stderr

    raw = run_git("cat-file", "-p", bad_name, cwd=tmp_path, binary=True)
    assert isinstance(raw.stderr, bytes)
    assert b"\xff" in raw.stderr


def test_cwd_selects_the_repository_and_none_keeps_the_process_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _init_repo(tmp_path)
    in_tmp = run_git("rev-parse", "--show-toplevel", cwd=tmp_path)
    assert Path(in_tmp.stdout.strip()).resolve() == tmp_path.resolve()

    monkeypatch.chdir(tmp_path)
    inherited = run_git("rev-parse", "--show-toplevel")
    assert Path(inherited.stdout.strip()).resolve() == tmp_path.resolve()


def test_timeout_is_forwarded_and_the_expiry_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, Any] = {}

    def fake_run(argv: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        seen.update(kwargs)
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    monkeypatch.setattr(_tool_common.subprocess, "run", fake_run)
    with pytest.raises(subprocess.TimeoutExpired):
        run_git("status", timeout=3)
    assert seen["timeout"] == 3


def test_missing_git_executable_propagates_file_not_found(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        run_git("--version")
