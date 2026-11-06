"""tools/_tool_common.py

Shared, non-CLI helper (same role as tools/_docs_consistency_lib.py): the repository
root, one `git` runner, and the exit-code constants of the CLI convention. Standard
library only, because deploy scripts import it through tools/manage_binaries.py with
the system python3.

`run_git` text mode decodes UTF-8 and replaces undecodable bytes; bytes mode returns
raw bytes for NUL-delimited output. `cwd=None` keeps the process working directory.
`OSError`, `subprocess.TimeoutExpired`, and (with `check=True`)
`subprocess.CalledProcessError` propagate, so each caller keeps its own handling.
"""

from __future__ import annotations

import subprocess  # nosec B404 — git is a trusted local CLI, argv is a fixed list
from pathlib import Path
from typing import Literal, overload

REPO_ROOT = Path(__file__).resolve().parent.parent

# CLI convention: 0 pass, 1 findings, 2 usage or environment error.
EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


@overload
def run_git(
    *args: str,
    cwd: Path | None = None,
    check: bool = False,
    binary: Literal[False] = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str]: ...


@overload
def run_git(
    *args: str,
    cwd: Path | None = None,
    check: bool = False,
    binary: Literal[True],
    timeout: float | None = None,
) -> subprocess.CompletedProcess[bytes]: ...


def run_git(
    *args: str,
    cwd: Path | None = None,
    check: bool = False,
    binary: bool = False,
    timeout: float | None = None,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    argv = ["git", *args]
    if binary:
        return subprocess.run(  # nosec B603 B607 — fixed git argv, no shell, no user-built command
            argv, cwd=cwd, capture_output=True, check=check, timeout=timeout
        )
    return subprocess.run(  # nosec B603 B607 — fixed git argv, no shell, no user-built command
        argv,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
        timeout=timeout,
    )
