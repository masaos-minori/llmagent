# Procedure: tools/complete_doc_procedure.py - unfinished-row refusal and sanctioned archival

## Goal

Make the completion tool refuse unfinished procedures before any write, and archive finished procedures through the shared sanctioned archival function so that staging, committing, and rename history are identical to every other work-item move.

## Scope
**Release unit**: N/A: not part of a release unit

- Replace the `DONE_DIR` copy-and-unlink archival with a call to `move_to_done` from `tools/manage_workitem_stage.py`. (REQ-001)
- Refuse `Pending`, `In Progress`, and `Blocked` rows after the tool's own update, before the first write, together with the existing taken-destination and missing-memo-line refusals. (REQ-002)
- Refuse a procedure that is not directly under `implementations/` as a usage error. (REQ-003)
- Keep a dry run refusing with the same exit code and writing nothing. (REQ-004)
- Insert the Verification Findings table as before, and remove the memo line after a successful move. (REQ-005)
- Stay inside the tool conventions: no subprocess, type hints, no function of radon grade C or worse, size gate. (REQ-008)

## Assumptions

- `move_to_done` with `stage_only=True` is enough: it stages the rewritten source (its `_auto_commit` runs `git add` for the uncommitted file) and then `git mv`s it; the tool never commits. (Plan Assumption)
- The unfinished set reuses `_UNFINISHED_STATUSES` from `tools/_workitem_status_table.py` by import; `tools/_workitem_stage_parser.py` is the verified precedent for importing a private name from that module.
- The location refusal (exit 2) is checked for any run; the unfinished-row refusal (exit 1) applies only when archiving (`--no-archive` keeps updating rows without it). (Plan Implementation Intent and Assumptions)
- `tools/complete_doc_procedure.py` has no importer; only `tools/TOOL_DESCRIPTIONS.md` and `tests/tools/test_complete_doc_procedure.py` name it.
- `tools/` is rsynced by `deploy.sh`; there is no deploy step for this change.

## Design decisions

- Refusal order inside `run`, all before the first write: location (usage error), the unfinished rows in the updated text, the destination, the memo line. The current code already computes everything before `_commit`; this change adds the row and location refusals and moves the memo edit to last (Plan Decision 2).
- Call `move_to_done(proc, kind="implementation procedure", stage_only=True)` as a function inside `_commit`. Alternative considered: run `manage_workitem_stage.py close-implementation` as a subprocess. Rejected: the command's `Pending`-only refusal duplicates a weaker check, its output would have to be parsed, and a subprocess cannot share one test repository (Plan Decision 1).
- The unfinished-row refusal is evaluated against the updated in-memory text (after `_complete_status_rows`), so a document whose only unfinished rows are the `Pending` rows about to be stamped still passes, and `In Progress` or `Blocked` rows that the stamping skips are caught.
- The memo line is removed after the archival move. The current `_commit` edits the memo before the archive write; reordering it makes a failing move never leave the memo without its line (Plan Decision 2).

## Alternatives considered

- Keep the `DONE_DIR` copy-and-unlink and only add the row check. Rejected: it keeps bypassing the sanctioned function, which is exactly the split the status-vocabulary Plan deferred to this change (`plans/done/20261117-124614_wftool002_status-vocabulary-unify.md`, UNK-04 resolution).
- Delegate the row check to `move_to_done` or `close-implementation`. Rejected: the sanctioned function has no row knowledge, and `close-implementation` refuses only `Pending` rows, missing `In Progress` and `Blocked` (Plan Decision 3 scope note).
- Apply the unfinished-row refusal also under `--no-archive`. Rejected: the Plan states `--no-archive` keeps updating rows without the refusal, which is the tool's repair path for an already-archived or in-place document.

## Implementation

### Target file

`tools/complete_doc_procedure.py` (exists, 9657 B)

### Procedure

1. Import `move_to_done` from `tools/manage_workitem_stage.py`, and extend the existing import from `tools/_workitem_status_table.py` with `pending_rows` and `describe_rows` (all existing names in those modules; nothing new is created in them). `IMPLEMENTATIONS_DIR`, currently imported unused, becomes the location anchor.
2. In `parse_args` (or immediately after it in `run`), refuse a procedure that is not directly under `implementations/` — `opts.proc.parent != IMPLEMENTATIONS_DIR` after resolution — with `DocProcedureError` exit 2, before any file is read. This also refuses documents already inside `implementations/done/`, which is what the plan's location test asserts.
3. Add `_unfinished_row_refusal(opts, updated_lines)` called in `run` after `_complete_status_rows` produces the updated lines and before `_commit`: when `opts.archive`, parse the table from the updated text with `parse_execution_status_rows`, and when `pending_rows(rows)` (the `_UNFINISHED_STATUSES` set) is non-empty, raise `DocProcedureError` exit 1 printing the offending rows via `describe_rows`, matching the message shape of `cmd_close_implementation` in `tools/manage_workitem_stage.py`.
4. Keep the existing taken-destination check (`_archive_destination`, exit 1) as a pre-flight: `move_to_done` only refuses a taken destination after it is called, so the tool must still check first and name the destination. `DONE_DIR` stays a module constant used by this check.
5. Rewrite `_commit` to the order: write the updated procedure in place with the existing `stage_write` call (keeping the staged-write model and removing only the `DONE_DIR` copy and the `opts.proc.unlink()`), call `move_to_done(opts.proc, kind="implementation procedure", stage_only=True)`, then apply the memo edit last. `run` must therefore pass the already-computed memo text into `_commit` instead of `_commit` editing the memo first.
6. `--dry-run` keeps calling `_preview` and returning before `_commit`, so it reports the same refusals (raised while computing memo text and destination) and moves, writes, and edits nothing (REQ-004).
7. Update the module docstring (it is the usage text printed on a usage error) to state the unfinished-row refusal, the location requirement, and the archival through `move_to_done`. Keep radon at grade B or better: the current maximum score is B (9) at `_complete_status_rows`; keep the refusal checks in small helpers rather than growing `run`.

### Method

Modify in place with targeted edits; no file split, no new module. The `parse_args` / `run` / `_preview` / `_commit` split introduced by the prerequisite Plan stays.

### Details

- Exit codes: 0 success; 1 refusals (unfinished rows, taken destination, missing memo line, missing anchor); 2 usage errors (unknown option, missing procedure, location). The unfinished-row refusal is a refusal (1), the location refusal a usage error (2), per REQ-002 and REQ-003.
- A refusal must leave the procedure, the memo, and `implementations/done/` byte-identical (AC-2): this holds because every refusal raises before `_commit` is reached, and the staged-write transaction resets the index and working tree in its `finally` block on any failure inside it.
- The Verification Findings insertion (`_insert_findings`) and the `--step1-note`/`--step2-note` behavior keep their current positions in the in-memory update pipeline.

## Compatibility considerations

- CLI surface unchanged: `--archive` default, `--no-archive`, `--dry-run`, `--memo`, `--vf`, step notes behave as documented.
- Behavior change: a run with archival on and an unfinished row now exits 1 with nothing written, where today it stamps and archives anyway. This is the intended change (AC-2) and is recorded in the tool description rows (see `implementations/20261118-070621_03_tools_TOOL_DESCRIPTIONS.md.md`).
- Behavior change: a procedure outside `implementations/` is now a usage error. Existing tests with root-level fixtures are restructured in `tests/tools/test_complete_doc_procedure.py` (see `implementations/20261118-070621_02_tests_tools_test_complete_doc_procedure.py.md`).
- The 580 archived procedures that already carry unfinished rows are untouched: the refusal gates new runs only, and they remain in `tools/check_archived_status_baseline.txt`.

## Security considerations

- No subprocesses, no shell, no dynamic execution; `bandit` must stay clean.
- Paths are resolved with the existing `_resolve` helper; `move_to_done` adds its own refuse-before-move checks (outside repository, already archived, taken destination, remote collision).

## Rollback considerations

- `git revert` of the single commit for this file restores the previous copy-and-unlink archival and the absence of the row refusal; already-archived procedures are unaffected by either implementation.
- No database, config, or service state is touched.

## Validation plan

- `uv run pytest tests/tools/test_complete_doc_procedure.py -v` (the tests defined in the companion test procedure; the refusal, archival, and location tests fail against the current code before this change).
- `uv run ruff format tools` and `uv run ruff check tools`.
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.
- `uv run radon cc tools/complete_doc_procedure.py -s -n C` reports nothing (no grade C or worse).
- `uv run bandit tools/complete_doc_procedure.py` reports no issue of medium or higher severity.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` passes (this tool is not a baseline member; current 9657 B of the 24576 B gate).
- Smoke run of `--dry-run` on a copy of a real archived procedure (plan Phase 5).

## Completion criteria

- AC-1: archival goes through `move_to_done` and no copy-and-unlink archival path remains (`rg` for the call, and for absence of `DONE_DIR` archival writes and `unlink`).
- AC-2: an unfinished procedure, archived, exits 1 listing the rows with nothing written.
- AC-3: a procedure outside `implementations/` exits 2 with nothing changed.
- AC-4: `--dry-run` refuses identically and writes nothing.
- AC-5: the memo line is removed only after a successful move and the findings table is inserted.
- AC-8: ruff, mypy, bandit, radon, and the size gate pass on the changed file.

## Out of Scope

- Changing `close-implementation` or `cmd_close_implementation` to refuse `In Progress` and `Blocked` rows (Plan UNK-01; a maintainer decision filed separately).
- Making the memo path configurable or moving memo handling out of the tool (Plan UNK-02).
- Other rows of `tools/TOOL_DESCRIPTIONS.md` and the tool's own test module (separate procedure documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-008
- **Source issue**: issues/20261117-132202_wftoolfu002_doc-procedure-archival.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-134130_wftoolfu002_doc-procedure-archival.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-070621
- **Related target files**: `tools/complete_doc_procedure.py`
