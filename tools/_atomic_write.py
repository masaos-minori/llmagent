"""tools/_atomic_write.py

Shared, non-CLI helper (same role as tools/_docs_consistency_lib.py): an atomic text
write, a staged two-phase write for changes that span two files, a unified-diff
dry-run preview, and the `--dry-run` option helper. Standard library only.

A write goes to a temporary file in the target's directory and is moved over the
target with `os.replace`, so an interruption before the replace leaves the original
untouched. Text is written as UTF-8 bytes without newline translation.
"""

from __future__ import annotations

import argparse
import difflib
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


def _default_file_mode() -> int:
    umask = os.umask(0)
    os.umask(umask)
    return 0o666 & ~umask


@dataclass(frozen=True)
class StagedWrite:
    """A temporary file holding the new content of `target`, not yet in place."""

    target: Path
    temp: Path

    def commit(self) -> None:
        if self.target.exists():
            shutil.copymode(self.target, self.temp)
        else:
            self.temp.chmod(_default_file_mode())
        os.replace(self.temp, self.target)

    def discard(self) -> None:
        self.temp.unlink(missing_ok=True)


def stage_write(path: Path, text: str, *, encoding: str = "utf-8") -> StagedWrite:
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(text.encode(encoding))
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return StagedWrite(path, temp)


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    staged = stage_write(path, text, encoding=encoding)
    try:
        staged.commit()
    except BaseException:
        staged.discard()
        raise


def render_diff(path: Path, old: str, new: str) -> str:
    return "".join(
        difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
        )
    )


def print_dry_run(path: Path, old: str, new: str) -> None:
    diff = render_diff(path, old, new)
    if not diff:
        print(f"{path}: no change")
        return
    print(diff, end="" if diff.endswith("\n") else "\n")


def add_dry_run_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the intended change as a diff and write nothing",
    )
