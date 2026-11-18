#!/usr/bin/env python3
"""tools/complete_doc_procedure.py - Record completion of a docs-wave procedure doc.

One call per documentation procedure document in the batch workflow:
  1. Sets the `### Execution Status` rows to `Completed` with timestamps (step 1 = the
     document edit, step 2 = the documentation checkers), filling the Notes cells.
  2. Inserts a `### Verification Findings` table (one row per --vf argument, format
     `ITEM|FINDING|ACTION`) before `### Blocker Log` when any --vf is given and the
     section does not already exist.
  3. With --archive: refuses a document that still carries an unfinished
     (`Pending`/`In Progress`/`Blocked`) row, requires the document to be directly under
     `implementations/` (otherwise a usage error), removes the document's line from MEMO
     (default memo3.md, matched by filename), and moves the procedure doc to
     `implementations/done/` through the sanctioned `move_to_done` (a staged `git mv`
     carrying the rewritten content). Refuses when the destination exists.

Every validation runs before anything is committed; the commit order is procedure
content, archive move, then memo line. The procedure rewrite and the archive move go
through `tools/_atomic_write.py` staged writes and `move_to_done`, so an interruption
leaves the original files untouched.

Usage:
    python tools/complete_doc_procedure.py PROC.md \\
        [--step1-note TEXT] [--step2-note TEXT] \\
        [--vf "ID|finding|action"]... [--memo PATH] [--no-archive] [--dry-run]

With --dry-run the same validations run, the intended procedure and memo diffs are
printed, the intended archive move is reported, and nothing is written, renamed, or
edited; the exit code is the one the real run would return.

`main(argv)` takes the argument list; `argv=None` means `sys.argv[1:]`.
Exit 0 on success, 1 on a refusal (unfinished row, taken destination, missing memo line
or anchor), 2 on a usage error (unknown option, missing procedure, or a document not
directly under `implementations/`).
"""

from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import print_dry_run, stage_write
from tools._workitem_status_table import (
    _UNFINISHED_STATUSES,
    COMPLETED_STATUS,
    parse_execution_status_rows,
)
from tools.manage_workitem_stage import move_to_done

REPO = Path(__file__).resolve().parent.parent
IMPLEMENTATIONS_DIR = REPO / "implementations"
DONE_DIR = IMPLEMENTATIONS_DIR / "done"

STATUS_ANCHOR = "### Execution Status"
FINDINGS_ANCHOR = "### Verification Findings"
BLOCKER_ANCHOR = "### Blocker Log"
FINDINGS_TABLE_HEAD = (
    "| Item | Finding | Action taken |",
    "|------|---------|--------------|",
)
_STEP_NOTE = re.compile(r"--step(\d+)-note")


class DocProcedureError(Exception):
    """The document, the memo, or the arguments are not in the shape the tool needs."""

    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


@dataclass
class Options:
    """Parsed command line. Paths are resolved against `REPO` when relative."""

    proc: Path
    step_notes: dict[int, str] = field(default_factory=dict)
    vfs: list[str] = field(default_factory=list)
    memo: Path = REPO / "memo3.md"
    archive: bool = True
    dry_run: bool = False


def _resolve(arg: str) -> Path:
    """Resolve a relative path against REPO; keep an absolute path as-is."""
    path = Path(arg)
    return path if path.is_absolute() else REPO / path


def _apply_option(opts: Options, argv: list[str], index: int) -> int:
    """Apply argv[index] to opts; returns the tokens consumed, 0 for an unknown option."""
    arg = argv[index]
    match = _STEP_NOTE.fullmatch(arg)
    if match:
        opts.step_notes[int(match.group(1))] = argv[index + 1]
        return 2
    if arg == "--vf":
        opts.vfs.append(argv[index + 1])
        return 2
    if arg == "--memo":
        opts.memo = _resolve(argv[index + 1])
        return 2
    if arg == "--no-archive":
        opts.archive = False
        return 1
    if arg == "--dry-run":
        opts.dry_run = True
        return 1
    return 0


def parse_args(argv: list[str]) -> Options:
    """Parse the argument list, raising DocProcedureError (exit 2) on a usage error."""
    if not argv:
        raise DocProcedureError(__doc__ or "", 2)
    opts = Options(proc=_resolve(argv[0]))
    if not opts.proc.is_file():
        raise DocProcedureError(f"procedure doc not found: {opts.proc}", 2)
    if opts.proc.parent != IMPLEMENTATIONS_DIR:
        raise DocProcedureError(
            f"procedure must be directly under implementations/: {opts.proc}", 2
        )
    index = 1
    while index < len(argv):
        consumed = _apply_option(opts, argv, index)
        if consumed == 0:
            raise DocProcedureError(f"unknown option: {argv[index]}", 2)
        index += consumed
    return opts


def _anchor_index(lines: list[str], anchor: str) -> int | None:
    """Index of the document line that is exactly this section anchor."""
    return next((i for i, line in enumerate(lines) if line.strip() == anchor), None)


def _complete_status_rows(
    lines: list[str], opts: Options, stamp: str
) -> tuple[list[str], int]:
    """Rewrite the `Pending` Execution Status rows; returns the lines and the row count."""
    head = _anchor_index(lines, STATUS_ANCHOR)
    if head is None:
        raise DocProcedureError(f"anchor not found: {STATUS_ANCHOR}", 1)
    rows = list(lines)
    changed = 0
    for index in range(head + 2, len(rows)):
        line = rows[index]
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6 or cells[2] != "Pending":
            continue
        step = int(cells[0]) if cells[0].isdigit() else changed + 1
        note = opts.step_notes.get(step, "")
        rows[index] = (
            f"| {cells[0]} | {cells[1]} | {COMPLETED_STATUS} | {stamp} | {stamp} | {note} |"
        )
        changed += 1
    if changed == 0:
        raise DocProcedureError("no Pending rows found in Execution Status", 1)
    return rows, changed


def _unfinished_row_refusal(opts: Options, updated_lines: list[str]) -> None:
    """Refuse archiving when the updated text still carries an unfinished row.

    Evaluated against the updated in-memory text (after stamping the `Pending` rows), so a
    document whose only unfinished rows are the `Pending` rows about to be stamped passes,
    while `In Progress`/`Blocked` rows that stamping skips are caught. No-op under
    `--no-archive` (the refusal is archive-scoped).
    """
    if not opts.archive:
        return
    rows = parse_execution_status_rows("\n".join(updated_lines) + "\n")
    if rows is None:
        return
    unfinished = [
        row for row in rows if row.get("Status", "").strip() in _UNFINISHED_STATUSES
    ]
    if unfinished:
        detail = "; ".join(
            f"Step {row.get('Step', '?')}: {row.get('Description', '?')} "
            f"({row.get('Status', '?')})"
            for row in unfinished
        )
        raise DocProcedureError(
            f"unfinished Execution Status rows before archiving: {detail}", 1
        )


def _insert_findings(lines: list[str], vfs: list[str]) -> list[str]:
    """Insert the findings table before `### Blocker Log` when `--vf` rows need a section."""
    if not vfs or any(line.strip() == FINDINGS_ANCHOR for line in lines):
        return lines
    blocker = _anchor_index(lines, BLOCKER_ANCHOR)
    if blocker is None:
        raise DocProcedureError(f"anchor not found: {BLOCKER_ANCHOR}", 1)
    table = [FINDINGS_ANCHOR, *FINDINGS_TABLE_HEAD]
    for vf in vfs:
        parts = vf.split("|", 2)
        if len(parts) != 3:
            raise DocProcedureError(f"--vf needs ITEM|FINDING|ACTION: {vf}", 2)
        table.append(f"| {parts[0]} | {parts[1]} | {parts[2]} |")
    rows = list(lines)
    rows[blocker:blocker] = [*table, ""]
    return rows


def _archive_destination(opts: Options) -> Path | None:
    """The archive destination, or None when archiving is off; refuses a taken destination."""
    if not opts.archive:
        return None
    dest = DONE_DIR / opts.proc.name
    if dest.exists():
        raise DocProcedureError(f"archive destination exists: {dest}", 1)
    return dest


def _memo_text(opts: Options) -> str | None:
    """Memo text with the procedure's line removed; None when the memo file is absent."""
    if not opts.memo.is_file():
        print(f"memo not found, skipped: {opts.memo}", file=sys.stderr)
        return None
    lines = opts.memo.read_text(encoding="utf-8").splitlines()
    kept = [line for line in lines if opts.proc.name not in line]
    if len(kept) == len(lines):
        raise DocProcedureError(f"no memo line matched: {opts.proc.name}", 1)
    return "\n".join(kept) + "\n"


def _preview(
    opts: Options, old: str, new: str, memo_new: str | None, dest: Path | None
) -> None:
    """Print the intended diffs and archive move; the caller writes nothing."""
    print_dry_run(opts.proc, old, new)
    if memo_new is not None:
        print_dry_run(opts.memo, opts.memo.read_text(encoding="utf-8"), memo_new)
    if dest is not None:
        print(f"dry run: would archive {opts.proc} -> {dest}")


def _commit(
    opts: Options,
    new_text: str,
    memo_new: str | None,
    dest: Path | None,
    changed: int,
) -> None:
    """Commit in order: procedure content, the sanctioned archive move, then the memo.

    The archive goes through `move_to_done` (a staged `git mv` carrying the rewritten
    content); the memo line is removed last so a failed move never leaves the memo without
    its line.
    """
    staged = [stage_write(opts.proc, new_text)]
    try:
        for write in staged:
            write.commit()
    except BaseException:
        for write in staged:
            write.discard()
        raise
    print(f"status updated: {changed} row(s); vf rows: {len(opts.vfs)}")
    if dest is not None:
        result = move_to_done(
            opts.proc, kind="implementation procedure", stage_only=True
        )
        if not result.success:
            raise DocProcedureError(f"archive failed: {result.error}", 1)
        print(f"archived: implementations/done/{opts.proc.name}")
    if memo_new is not None:
        memo_write = stage_write(opts.memo, memo_new)
        try:
            memo_write.commit()
        except BaseException:
            memo_write.discard()
            raise
        print(f"memo line removed: {opts.proc.name}")


def run(opts: Options) -> None:
    """Validate everything first, then preview (dry run) or commit the change."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    old = opts.proc.read_text(encoding="utf-8")
    rows, changed = _complete_status_rows(old.splitlines(), opts, stamp)
    rows = _insert_findings(rows, opts.vfs)
    new_text = "\n".join(rows) + "\n"
    _unfinished_row_refusal(opts, rows)
    dest = _archive_destination(opts)
    memo_new = _memo_text(opts) if opts.archive else None
    if opts.dry_run:
        _preview(opts, old, new_text, memo_new, dest)
        return
    _commit(opts, new_text, memo_new, dest, changed)


def main(argv: list[str] | None = None) -> int:
    """Entry point: complete one procedure document; `argv=None` means `sys.argv[1:]`."""
    try:
        run(parse_args(sys.argv[1:] if argv is None else argv))
    except DocProcedureError as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
