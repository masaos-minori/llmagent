# Implementation Procedure: `detect-unexecuted-archive` subcommand in manage_workitem_stage.py

## Goal

Add a read-only, report-only `detect-unexecuted-archive` subcommand to
`tools/manage_workitem_stage.py` implementing `REQ-002`. It enumerates
`implementations/done/*.md`, computes each procedure's archive date (the first commit that
added the file at its `implementations/done/` path), parses its `### Execution Status`
rows, and reports every procedure archived within the last N days that still carries a
`Pending`, `In Progress`, or `Blocked` row. Procedures archived longer ago are skipped, and
the command never moves or edits a work item and always exits 0. (`REQ-002`: the detector
warns on recent stale archives, never on older ones, and never modifies a work item.)

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The repository root is the current working directory; the tool scans relative paths
  (`implementations/done/`), as every other subcommand does.
- The archive date is recoverable as the first commit that added the file at its
  `implementations/done/` path via `git log --diff-filter=A`; a procedure with no such
  commit (tracked before git, or after a history rewrite) is skipped, not reported.
- Window N defaults to 7 days (matching the existing `detect-stale` default) and is
  configurable via a `--days` flag. (`UNK-01`)
- The detector is owned as a subcommand of this tool, not a standalone tool, so it needs no
  `TOOL_DESCRIPTIONS.md` row and no `check_tool_descriptions_sync.py` gate. (`UNK-02`)

## Design decisions
- **Ownership = subcommand, co-located with `detect-stale`**: add the subcommand to this
  file and register it in `build_parser()` (`tools/_workitem_stage_parser.py`), reusing the
  file's `parse_execution_status_rows` and the `close-implementation` `Pending` refusal it
  complements. A standalone tool under `tools/` is acceptable only if the implementation
  phase prefers isolation, but then it needs a `TOOL_DESCRIPTIONS.md` row and the "Adding a
  new tool" validation in `routing.md`. (`UNK-02`; see Reference Files)
- **Basis = archive date, not mtime**: compute each file's archive date as the timestamp of
  the first commit that added it at its `implementations/done/` path
  (`git log --diff-filter=A --format=%cI -1 -- <done-path>`), and compare against
  `now - timedelta(days=N)`. This distinguishes a mistake made today from the historical
  `done/` procedures that already carry stale rows, satisfying the constraint that old
  archives produce no finding.

## Alternatives considered
- Reusing `detect-stale`'s mtime basis: rejected; mtime cannot distinguish a recent
  mistake from the dozens of historical `done/` procedures that already have stale rows.
- Reporting via non-zero exit so CI can fail: rejected; `REQ-002` requires exit 0 and a
  report-only signal, so findings are printed to stdout and the process still exits 0.
- Modifying `close-implementation` to also refuse on archive date: rejected; that changes a
  refusal condition beyond what `REQ-002` needs and risks breaking batch archive.

## Implementation
### Target file
`tools/manage_workitem_stage.py`

### Procedure
1. **Parser registration** — in `tools/_workitem_stage_parser.py`, inside `build_parser()`,
   add a new subparser after the `detect-stale` block:
   - name `detect-unexecuted-archive`, help `"Report recently-archived procedures with open Execution Status rows"`.
   - argument `--days` (`type=int`, `default=7`, help matching the `detect-stale` flag).
2. **Command function** — in `tools/manage_workitem_stage.py`, add `cmd_detect_unexecuted_archive` (new)(args) returning `int`:
   - Resolve the repo root from the current working directory (the same basis every `_get_*` helper uses).
   - Enumerate `Path("implementations") / "done" / "*.md"` (skip if the directory is absent).
   - Compute every in-window archive date in a SINGLE `git log` pass rather than one
     `git log` per file: run
     `git log --no-renames --diff-filter=A --since=@<epoch> --format=%cI --name-only -- "implementations/done/*"`
     from the repo root, where `<epoch>` is `int((now - timedelta(days=args.days)).timestamp())`,
     then group the emitted `(date, path)` pairs by path and keep the earliest date per path.
     A per-file `git log` would walk full history once per file (~8k files here, hours); the
     `--since` filter restricts git to the window, keeping this to one cheap scan.
     `--no-renames` is required: procedures reach `done/` via `git mv`, which git records as a
     rename (R); `--diff-filter=A` alone skips every such archive and would report nothing.
     Pairs whose path has no add-commit inside the window are simply absent from the output
     (skipped, not reported).
   - If the archive date is older than the window, skip.
   - Otherwise parse the file's `### Execution Status` table with `parse_execution_status_rows`; collect rows whose `Status` is `Pending`, `In Progress`, or `Blocked`.
   - If any such row exists, record `(path, archive_date, statuses)` as a finding.
   - After the loop: if no findings, print a one-line "no unexecuted archives found (window: N days)" message; else print a header and one line per finding. Always `return 0`.
   - Use `datetime`/`timedelta`/`UTC` explicitly (`from datetime import UTC, datetime, timedelta` at module top) instead of the `__import__` pattern used by `cmd_detect_stale`.
3. **Dispatch** — in `main()`, add an `elif args.subcommand == "detect-unexecuted-archive": return cmd_detect_unexecuted_archive(new)(args)` branch after the `detect-stale` branch.
4. **Help text** — document in the subcommand help that procedures with no archive-date commit are skipped and that the command is report-only (never moves or edits a file).

### Method
- Add a new function and a new parser branch; do not alter existing functions, signatures, or the `close-implementation` refusal.
- Keep the new command's output format consistent with `cmd_detect_stale` (a header line plus one `  [kind] path: status`-style line per finding).

### Details
- Reuse `parse_execution_status_rows` (already imported/defined in this module) for the
  Execution Status parse; do not re-implement table parsing.
- Treat the three statuses case-sensitively against the canonical values defined in
  `_workitem_status_table._VALID_STATUSES` (`Pending`, `In Progress`, `Blocked`); normalize
  via `_normalize_status` if a raw variant is seen.
- Guard the `git log` call so a missing `.git` or a path with no history results in a skip
  (print nothing for that file), never an exception.

## Compatibility considerations
- Backward compatible: a new subcommand does not change any existing command's behavior,
  arguments, or exit codes. Existing tests must still pass (regression).
- The `main()` dispatch gains one `elif` branch; the `else` fallback still prints help and
  returns 1 for unknown subcommands.

## Security considerations
- Read-only: the command performs no write, move, or edit. It runs `git log` (read-only)
  and reads files. No permission escalation.
- No secrets or credentials are read or logged; only file paths and status strings are printed.

## Rollback considerations
N/A: revert the commit; the change is additive and isolated to one new subcommand.

## Validation plan
- Unit: detector over a temporary repository (see companion test doc) — recent archive with
  a stale row is reported; recent archive with all rows completed is not; old archive with a
  stale row is not; no file is moved; exit code is 0.
- Regression: existing `manage_workitem_stage.py` tests pass unchanged.
- Smoke: run `uv run python tools/manage_workitem_stage.py detect-unexecuted-archive` on the
  live `implementations/done/`; confirm it exits 0 and the historical `done/` files produce
  no finding.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy tools/manage_workitem_stage.py`, `uv run bandit tools/manage_workitem_stage.py`.
- Gate: `check_tool_descriptions_sync.py` passes (no new standalone tool was added).

## Completion criteria
`tools/manage_workitem_stage.py` exposes a `detect-unexecuted-archive` subcommand that
reports only procedures archived within N days (default 7) that still have a
`Pending`/`In Progress`/`Blocked` Execution Status row, skips older and un-datable
procedures, never moves or edits a file, and exits 0; existing commands are unchanged.

## Out of Scope
- Editing `tools/plan_dependency_order.py` here (its own row covers `REQ-003`).
- Editing `tools/check_workitem_traceability.py` here (reference only; ownership stays a
  subcommand of this tool).
- Adding a `TOOL_DESCRIPTIONS.md` row (only needed if the implementation phase chooses a
  standalone tool).
- Changing the `close-implementation` `Pending` refusal condition.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Register the `detect-unexecuted-archive` subcommand in the parser | Completed | 20261107-141528 | 20261107-141528 |  |
| 2 | Implement `cmd_detect_unexecuted_archive` (new) (archive-date basis, report-only) | Completed | 20261107-141528 | 20261107-141528 |  |
| 3 | Wire the dispatch branch into `main()` | Completed | 20261107-141528 | 20261107-141528 |  |
| 4 | Add detector tests to the companion test file | Completed | 20261107-143853 | 20261107-143853 |  |
| 5 | Run the validation sequence (`rules/toolchain.md`) + smoke on live `done/` | Completed | 20261107-141528 | 20261107-141528 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` — add a read-only archive-date detector to manage_workitem_stage.py
- **Source issue**: `issues/20261106-123521_procarch001_archive-procedures-only-after-execution.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-121954_procarch001_archive-procedures-only-after-execution.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261107-125900
- **Related target files**: `tools/manage_workitem_stage.py`

## Reference Files (do not modify)
- `tools/_workitem_stage_parser.py` — register the new subcommand in `build_parser()` (after the `detect-stale` block, lines ~169-179).
- `tools/_workitem_status_table.py` — reuse `parse_execution_status_rows` and `_normalize_status` for the Execution Status parse.
- `templates/execution-status.md` — exact `### Execution Status` table columns and the `Pending`/`In Progress`/`Blocked` status vocabulary.
- `tools/check_workitem_traceability.py` — read to confirm detector ownership; recommended outcome is a subcommand of this tool, so this file is NOT modified.
- `rules/toolchain.md` — validation sequence for the tool change.