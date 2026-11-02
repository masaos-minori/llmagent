## Goal
- Create `tools/close_procedures_batch.py`, one command that verifies, then archives executed implementation procedures with renames staged, updates the Plan's `Work Items Created` rows, and marks named Plan steps `Completed` only on verified evidence (`REQ-002`: verify before change and dry run; `REQ-003`: staged archive, per-file failure isolation; `REQ-004`: explicit, verified Plan step marking; `REQ-005`: `Work Items Created` update).

## Scope
- In scope: the new tool module only. Its tests are the procedure for `tests/tools/test_close_procedures_batch.py`; skill text and registration are the procedures for rows 03 to 05.
- The tool imports helpers from `tools/manage_workitem_stage.py` and `tools/set_execution_status.py`; neither file is modified.

## Assumptions
- Plan A1, A2, A4, A10 apply. A2: a new sibling tool, not a `manage_workitem_stage.py` subcommand. A4: Plan steps are marked only when the caller names them. A10: `set_execution_status.apply_updates` completes every selected row regardless of status, so the tool selects only the step numbers of `Pending` rows.
- Step 3a verified (2026-11-02): `move_to_done(source, *, kind, stage_only)` and `update_execution_status(source, kind, step_number, ..., new_status, new_notes, new_started, new_completed)` exist in `tools/manage_workitem_stage.py` (the second returns `bool` and prints its own error to stderr); `parse_execution_status_rows(content)` returns row dicts keyed by the header or `None`; `tools/set_execution_status.py` exposes `update_document(path, steps, notes, date)`, `ExecutionStatusError`, and `EMPTY_CELL`. No existing helper parses the `### Work Items Created` table, so this tool parses and rewrites it itself. `move_to_done` refuses a missing destination `done/` directory, an existing destination, and a remote-branch conflict, and with `stage_only` stages a dirty source before `git mv`.
- Step 3a verified: `N/A` is not in the status vocabulary of `templates/execution-status.md` or `_VALID_STATUSES`, but older archived procedures use it, so the verifier accepts `Completed` and `N/A` as terminal and never writes `N/A`.
- Step 3a verified: tools that run as scripts and import siblings use the `if __package__ in (None, ""): sys.path.insert(0, ...)` guard before `from tools.<module> import ...` (for example `tools/check_adr_invariant_matrix.py`); tests import tools as `tools.<module>`. `tests/tools/` has no `__init__.py`.
- Step 3a verified: a similar one-off, `tools/close_wflease001_procedures.py`, exists and is listed in `tools/TOOL_DESCRIPTIONS.md` as a reproducible record of one batch; it hard-codes completion of every row and per-procedure notes, so it does not cover the Plan's verification, mapping, or `Work Items Created` work. Left unchanged.
- Overlap (Plan Assumptions A5 to A7, A9): this row is a new file, so there is no overlap on the file itself. Its related sibling is the Plan `plans/20261102-080336_flowimp002_plan-release-units.md` procedure for batch mode, which defers Step 7 to the end of a release unit; this tool is what that deferred Step 7 would call, and needs no change for it.
- `Related target files` of earlier procedures can list companion test files after the primary target, as a comma-separated list (Plan Design, Matching); the tool splits on commas and strips backticks.

## Design decisions
- Two phases per run: `verify` over all named procedures (pure, no writes), then `apply` for verified ones only. A dry run prints the verify result and the intended changes and stops. Refused procedures are reported with the reason and left untouched; they never block verified ones.
- Pure helpers plus thin I/O: `parse_plan_steps` (new), `parse_related_targets` (new), `verify_procedure` (new), `update_work_items` (new), `check_step_marking` (new) are pure functions over text and are unit-testable without git; `apply_*` functions do the writes.
- Exit status: 0 when nothing was refused or failed, 1 otherwise, so a script can stop on a partial batch. Plan-step "left unchanged" is reported but does not make the exit non-zero.

## Alternatives considered
- A `manage_workitem_stage.py` subcommand: rejected (Plan A2).
- Automatically marking every step whose cited files are all archived: rejected (Plan A4); it is listed as a candidate only.
- Calling `close-implementation` through a subprocess: rejected; `move_to_done` is imported directly so a failure is a returned `MoveResult`, not an exit code to parse.

## Implementation
### Target file
`tools/close_procedures_batch.py` (new)

### Procedure
1. Create the module docstring (purpose, usage, behavior of each option, the step mapping rule), `from __future__ import annotations`, and the `sys.path` guard.
2. Implement `parse_related_targets(content) -> list[str]` (new) and `parse_source_plan(content) -> str | None` from the procedure's Traceability block (`- **Related target files**:` and `- **Source plan**:` lines).
3. Implement `verify_procedure(path, *, complete_rows, plan_path) -> ProcedureCheck` (a new dataclass) that never writes: file exists; `parse_execution_status_rows` returns rows; every row status is `Completed` or `N/A`, or, when the complete-rows flag is true, `Pending` is also allowed and recorded in the pending-steps list; a `Pending` row without the option, or any `Blocked` or `In Progress` row, refuses the procedure and names the row; the destination `implementations/done/<name>` does not exist and `implementations/done/` is a directory; the Plan resolves (explicit `--plan`, else the common `Source plan` of all named procedures, searched in `plans/` then `plans/done/`).
4. Implement `parse_plan_steps(plan_text, target_paths) -> list[PlanStep]` (new): read the numbered `Implementation steps` list; for each numbered item, collect the backticked `File Path` values from the item and its checkbox lines that match a row of the Plan's `Implementation Target Files` table. A step that cites no table path is reported as unparseable and is never marked.
5. Implement `check_step_marking(step, archived_paths) -> str | None` (new): returns a reason when any cited path has no archived procedure, where "archived" means a procedure in `implementations/done/` with the same `Source plan` (`plans/<f>` and `plans/done/<f>` count as the same) whose `Related target files` contain the path, or a procedure archived earlier in this run.
6. Implement the Work Items Created update as `update_work_items(plan_text, archived: dict[str, str]) -> tuple[str, list[str]]` (new): find `### Work Items Created`, and for each data row whose Item ID contains an archived procedure's original path set the Status cell to `Completed`; return unmatched paths for the report (no failure).
7. Implement `apply_procedure(check, *, complete_rows, note, stamp) -> ApplyResult`: when the pending-steps list is non-empty, call `tools.set_execution_status.update_document(path, set(pending_steps), {step: note ...}, stamp)`; then `move_to_done(path, kind="implementation procedure", stage_only=True)`; record the result; a failure is returned, never raised.
8. Implement `main(argv)`: argparse (`procedures...`, `--plan`, `--plan-steps`, `--complete-rows`, `--note`, `--dry-run`); `--complete-rows` without `--note` is a usage error. After applying, update the Plan once: Work Items Created rows, then each named step through `update_execution_status(plan, "plan", step_number=N, new_status="Completed", new_completed=stamp)` only when `check_step_marking` (new) returns `None`; with no `--plan-steps`, print candidate steps whose cited files are all archived and change none.
9. Print a plan-of-changes table in dry run, an applied-changes table otherwise, and a final line with counts: verified, refused, archived, failed, steps marked, steps left.

### Method
- `stamp` is `datetime.now().strftime("%Y%m%d-%H%M%S")`, the format `templates/execution-status.md` requires for Started and Completed.
- Dry run computes archive-destination freeness and step-marking verdicts exactly as the real run does, treating every verified procedure as archived, so its output equals what a real run would do.
- Write the Plan file once for the table update and use `update_execution_status` for steps, which rewrites the file; run the table update first, then the steps, re-reading the file between them.

### Details
- Archiving a procedure whose own rows were just completed stages the modified file before `git mv` (`stage_only=True`), so the staged rename carries the completed rows.
- A failed archive after `update_document` completed rows leaves those rows `Completed` in the unarchived file; the report says so, and the tool does not revert (rows were completed on the caller's explicit option).
- A Plan already in `plans/done/` is edited in place; the working-tree edit stays unstaged and is committed with the batch (`git-commit-and-sync`).
- Never touch a procedure that was not verified, and never commit.

## Compatibility considerations
- `close-batch`, `close-implementation`, `set-step-status`, `set_execution_status.py`, and `close_procedure.sh` are unchanged and keep working. The new CLI is additive.
- Status vocabulary is unchanged; the tool writes only `Completed`.

## Security considerations
- Paths come from the command line and are used only for local file reads, writes, and `git mv` through GitPython; no shell is invoked. Restrict procedure paths to files under `implementations/` and reject others so a mistyped path cannot archive an unrelated file.

## Rollback considerations
- Revert the commit that adds the file. A run's staged renames are reversible with `git restore --staged` and `git mv` back; the tool never commits.

## Validation plan
- `uv run pytest tests/tools/test_close_procedures_batch.py -v` (row 02 procedure).
- `uv run ruff format tools/close_procedures_batch.py`, `uv run ruff check tools/close_procedures_batch.py`, `uv run mypy tools/close_procedures_batch.py`, `uv run bandit tools/close_procedures_batch.py`.
- One live `--dry-run` on already-archived procedures of a recently closed Plan (for example the `20261101-165312` batch with its `plans/done/` Plan) and review against the manual result; confirm nothing changed with `git status`.

## Completion criteria
- A dry run prints every intended change and changes nothing; a real run applies exactly those changes with renames staged and no commit.
- A `Pending` or `Blocked` row refuses its procedure with the row named and no file changed; rows are completed only with `--complete-rows` and `--note`.
- One failed archive does not stop the others; a step is marked only when named and all cited files have archived procedures; candidates are listed when none is named.
- The lint, type, and security commands above are clean on the new file.

## Out of Scope
- Changing `close-batch`, `set_execution_status.py`, `close_procedure.sh`, or `manage_workitem_stage.py`.
- Generating procedures, deciding execution order, committing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `tools/close_procedures_batch.py` per Implementation > Procedure steps 1 to 9 | Completed | 20261102-132152 | 20261102-132503 | Changed: tools/close_procedures_batch.py (new). Stale detector clean, step 3a claims verified (move_to_done, update_execution_status, update_document exist). Row matching is exact on the backticked Item ID (not substring) so a name ending .md.md is not matched by its .md prefix. |
| 2 | Add tests per Validation plan (carried out by the row 02 procedure for `tests/tools/test_close_procedures_batch.py`) | Completed | 20261102-132503 | 20261102-132503 | Tests landed via procedure 02 (tests/tools/test_close_procedures_batch.py): 40 passed; testmon-forceselect run: 40 passed, 1 known pre-existing mdq failure. Full suite deferred to plan end. |
| 3 | Run the tool lint sequence (ruff format, ruff check, mypy, bandit) and the live dry run (`routing.md` Tools "Adding a new tool") | Completed | 20261102-132503 | 20261102-132503 | ruff format/check clean, mypy tools/close_procedures_batch.py clean, bandit 0 issues, check_mock_patch_targets, check_tool_descriptions_sync, skills checkers Pass. Live dry run on this plan's procedures and live repo: printed plan-of-changes, git status unchanged. Full suite deferred to plan end. |
| 4 | Register the tool in `tools/TOOL_DESCRIPTIONS.md` (carried out by the row 05 procedure) | Completed | 20261102-132503 | 20261102-132503 | Registered in tools/TOOL_DESCRIPTIONS.md in this cycle before archive (content of procedure 05); check_tool_descriptions_sync passes. |

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
- **Requirement ID**: `REQ-002` (verify before change, dry run), `REQ-003` (staged archive, failure isolation), `REQ-004` (explicit verified step marking), `REQ-005` (`Work Items Created` update)
- **Source issue**: issues/20261030-191530_flowimp008_workitem-bulk-close.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080631_flowimp008_workitem-bulk-close.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085613
- **Related target files**: tools/close_procedures_batch.py
