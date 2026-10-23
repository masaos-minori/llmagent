## Goal

Add a `close-batch` subcommand to `tools/manage_workitem_stage.py` that, given a batch's identifier, archives every procedure of that batch and marks the owning plan's `### Execution Status` rows `Completed`, leaving the result ready for a single `chore:` commit — replacing the repeated manual sequence of one `close-implementation` per file plus a plan-table update. (`REQ-001`–`REQ-007`)

## Scope

- **In-Scope**: implement the `close-batch` subcommand inside `tools/manage_workitem_stage.py` only — batch discovery, the atomic `Pending` pre-check, marking each procedure's rows `Completed`, archiving via the existing code path, the plan-status update, `--dry-run`, `--stage-only`, and idempotency. (`REQ-001`–`REQ-007`)
- **Out-of-Scope**: writing the tests (that is `tests/tools/test_manage_workitem_stage.py`, seq 02), registering the tool in `tools/TOOL_DESCRIPTIONS.md` (seq 03), referencing it from `skills/code-implementation/workflow.md` (seq 04), generating the commit message or running `git commit`, changing the `### Execution Status` table format or `templates/execution-status.md`, or touching any other workflow stage.

## Assumptions

- A batch is identified by a shared timestamp prefix embedded in `implementations/<prefix>_NN_*.md` filenames (confirmed across historical commits, e.g. `20261023-112037_*`); the same prefix appears in the owning plan's `Implementation Target Files` table.
- Each historical batch corresponds to one plan, so marking that plan's rows `Completed` is safe (re-verify against current `plans/done/` — UNK-03).
- The command imports the stable public functions of this module rather than re-implementing archival or table-editing logic.
- Stamp `Started`/`Completed` with `date +%Y%m%d-%H%M%S` (`YYYYMMDD-HHMMSS`) to match the `close-*` family and the historical batch-close commits, not `set_execution_status.py`'s `YYYY-MM-DD` (resolves UNK-02).

## Design decisions

- **Subcommand on the existing module, not a separate tool.** Add `close-batch` as a subcommand of `manage_workitem_stage.py`. It reuses `move_to_done()` (auto-commit, remote-conflict check, `--stage-only`), the argparse conventions, and `_report_move_result()`, and keeps the `close-*` family together. A separate `tools/close_batch.py` would duplicate the move plumbing the family already shares.
- **Atomic ordering.** Discover the whole batch first, run the `Pending` pre-check across every procedure, then mark all rows `Completed`, then archive each file. A failure mid-batch can therefore never leave a partially archived batch, and the destructive `git mv` never runs against a batch that failed its pre-check.

## Alternatives considered

- Separate `tools/close_batch.py`: rejected above — duplicates `move_to_done()`/parser plumbing the `close-*` family already shares.
- Marking rows via `set_execution_status.py` instead of `update_execution_status()`: rejected — different date format (`YYYY-MM-DD`) and it is a separate tool; `update_execution_status()` keeps the timestamp convention consistent with the rest of this module.

## Implementation

### Target file

`tools/manage_workitem_stage.py` (modify)

### Procedure

Implement in three phases mirroring the plan's Implementation steps.

**Phase 1 — Discovery + dry-run.** Add the `close-batch` subcommand skeleton: a positional batch id (a plan path or a bare timestamp prefix), plus `--dry-run` and `--stage-only`. Implement batch discovery from both input forms in sorted order.

**Phase 2 — Pending check + mark/archive + plan status.** Add the atomic `Pending` pre-check across all discovered procedures (refuse with no file moved when any row is `Pending`). Mark each procedure's `### Execution Status` rows `Completed` with `YYYYMMDD-HHMMSS`, then archive each via `move_to_done()`. Update the owning plan's `### Execution Status` rows to `Completed`. Add an idempotency guard for an already-closed batch.

**Phase 3 — Registration + validation** is covered by seq 03/04; this file's part is the code plus its own validation sequence (see Validation plan).

### Method

1. **Batch discovery (`REQ-001`).** Add helpers `_batch_prefix(batch_id: str) -> str` and `_discover_batch(batch_id: str, prefix: str) -> list[Path]`. `_discover_batch` returns the live procedure paths in `implementations/` in sorted order, with two input forms:
   - Plan path: derive the batch prefix from the plan's filename — the `<timestamp>` before `_plan.md` (via a new `_prefix_from_plan_path` helper); glob `implementations/<prefix>_*.md`.
   - Bare timestamp prefix: glob `implementations/<prefix>_*.md` directly.
   When live files exist, return them sorted. When none are live but they exist under `implementations/done/`, raise `AlreadyClosedBatch(archived_paths)` so the caller reports an already-closed no-op (exit 0); otherwise raise `BatchResolutionError` so the caller prints it and exits 1.
   **Owning plan.** Find the plan that owns the batch by (1) preferring a plan whose content references `implementations/<prefix>_`, then (2) falling back to a plan sharing the batch's `Source issue` (parsed from a procedure via a new `_extract_source_issue` helper). Search **both** `plans/*.md` and `plans/done/*.md` and return the first match, or `None` when no plan owns the batch.
2. **`Pending` pre-check (`REQ-002`).** For each discovered procedure, call `parse_execution_status_rows()` (already at `:308`) and collect any `Pending` rows via the existing `_pending_rows()` helper. If any exist, print the block message (reuse `_describe_rows()`, already at `:356`) and return exit 1 before touching any file.
3. **Mark + archive (`REQ-003`, `UNK-02`).** For each discovered procedure, call `update_execution_status(source=..., kind="implementation-procedure", new_status="Completed", new_started=<ts>, new_completed=<ts>)` (already at `:380`) to stamp `Started`/`Completed`, then archive via `move_to_done(source, kind="implementation procedure", stage_only=args.stage_only)` (already at `:235`). Pass `--stage-only` through to the archival move.
4. **Plan status (`REQ-004`).** Call `update_execution_status(source=<plan_path>, kind="plan", new_status="Completed", new_started=<ts>, new_completed=<ts>)` on the owning plan found in step 1.
5. **Dry-run (`REQ-005`).** When `--dry-run` is set, print every planned move (`source -> done/`) and every planned edit (procedure + plan rows) and return without calling `update_execution_status()` or `move_to_done()`.
6. **Idempotency (`REQ-007`).** After a successful run the batch's files no longer exist under `implementations/`, so a second discovery finds nothing and the run reports "already closed" as a no-op rather than a partial re-run. Guard the plan-row update so re-marking already-`Completed` rows does not double-stamp.
7. **Wire into the parser/dispatch.** Register `close-batch` in `build_parser()` (already at `:713`) alongside the other `close-*` parsers, giving it the same `--stage-only` flag every `close-*` already carries (at `:719`–`:766`), and add the dispatch branch in `main()` (already at `:1063`). Route output through `_report_move_result()` (already at `:597`) where it fits, or print a dedicated summary.

### Details

- Reuse the existing symbols rather than reimplementing them: `move_to_done()` (`:235-305`), `update_execution_status()` (`:380-525`), `parse_execution_status_rows()` (`:308-349`), `_pending_rows()` (`:352`), `_describe_rows()` (`:356`), `_report_move_result()` (`:597-609`), `build_parser()`/`main()` (`:713-1085`).
- The batch-id positional argument accepts both forms; disambiguate by testing `Path(batch_id).is_file()` first (plan path), else treat as a bare timestamp prefix.
- Plan-path discovery derives the prefix from the plan's filename stem, which only matches the batch when the plan and its procedures share a timestamp. In this repository the procedures carry a fresh generation timestamp (`20261023-233058_*`) that differs from the plan's (`20261023-222901`), so the bare-prefix form is the reliable entry point and the plan-path form is best-effort.
- Keep the atomic ordering even in `--dry-run`: discover and pre-check first, then print the intended moves/edits — a dry-run of a batch with a `Pending` row must report the block, not a clean plan.
- The owning-plan lookup scans `plans/*.md` **and `plans/done/*.md`** (a plan may already be archived) for a content reference to `implementations/<prefix>_`, falling back to a shared `Source issue`; return the first match. Do not try to identify the owner via the plan's `Implementation Target Files` table — that table lists the plan's code/test/doc targets, not the batch's procedures (this was the original Step 3a finding).

## Compatibility considerations

The change is additive: a new subcommand and two private helpers. No existing subcommand, function signature, or public contract changes, so existing `close-issue`/`close-plan`/`close-implementation`/`set-status`/`set-step-status` behavior is unaffected. The new helpers are module-private (leading underscore) and not referenced elsewhere.

## Security considerations

No new network, credential, or privilege surface. The command shells out to `git mv`/`git add`/`git commit` through the same `move_to_done()` path the other `close-*` commands use, so pre-commit hooks still run and no bypass flag is introduced. `--stage-only` stages rather than commits but does not alter the auto-commit safety semantics.

## Rollback considerations

Revert the commit that adds the `close-batch` subcommand. Because this is a single additive change to one file, `git checkout -- tools/manage_workitem_stage.py` (or reverting the commit) fully restores the prior state; no migration or data rollback is required.

## Validation plan

- Unit test batch discovery from both inputs (plan path and timestamp prefix), the `Pending` refusal, idempotency, and dry-run (`tests/tools/test_manage_workitem_stage.py`).
- An integration-style test using a temporary git repository fixture that archives a synthetic batch and asserts the plan rows are updated and the files moved (`move_to_done()` runs against the temp repo).
- `uv run ruff format` / `ruff check` / `ruff check --fix` clean on `tools/manage_workitem_stage.py`.
- `uv run mypy tools/manage_workitem_stage.py` and `uv run bandit tools/manage_workitem_stage.py` clean.
- `uv run python tools/check_workitem_structure.py` passes on this generated procedure document.
- Smoke run against current `implementations/` and `plans/` on a scratch branch; record the working-tree diff shape vs the historical batch-close commit `46078e90f` as evidence.

## Completion criteria

- `close-batch` is registered in `build_parser()` and dispatched in `main()`, accepting a plan path or timestamp prefix and carrying `--dry-run` and `--stage-only`.
- A batch with a `Pending` row is refused with no file moved; a clean batch is fully archived and its plan rows marked `Completed` with `YYYYMMDD-HHMMSS` timestamps in one invocation.
- A second invocation on an already-closed batch is a no-op or a clear refusal, not a partial re-run.
- `--dry-run` changes no file and lists every planned move and edit.
- `ruff`, `mypy`, and `bandit` are clean on the modified file.

## Out of Scope

Tests (`tests/tools/test_manage_workitem_stage.py`), the `tools/TOOL_DESCRIPTIONS.md` registration row, the `skills/code-implementation/workflow.md` reference pointer, commit generation, and any change to `templates/execution-status.md` or the `done/` directory structure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `close-batch` subcommand: discovery, `Pending` pre-check, mark/archive via `move_to_done()`/`update_execution_status()`, plan-status update, `--dry-run`, `--stage-only`, idempotency | Completed | 20261024-003320 | 20261024-004517 | REQ-001..REQ-007; tools/manage_workitem_stage.py. Stale detection clean (workflow Step 2). Step 3a corrections vs original procedure: owning-plan scan now includes `plans/done/`; owner identified via shared `Source issue` (primary: content reference to `implementations/<prefix>_`), not the plan's `Implementation Target Files` table; batch prefix derived from the plan filename stem. See Final Report. |
| 2 | Add tests per Validation plan | Pending | — | — | REQ-001, REQ-002, REQ-005, REQ-007; tests/tools/test_manage_workitem_stage.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff, mypy, bandit, check_workitem_structure.py |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: registration is seq 03/04 |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`, `REQ-005`, `REQ-006`, `REQ-007`
- **Source issue**: `issues/20261023-173429_workitem001_single-command-to-close-an-executed-implementation-batch-and-its-plan-status.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-222901_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-233058
- **Related target files**: `tools/manage_workitem_stage.py`
