## Goal
Split `manage_workitem_stage.py` by responsibility: move the Execution Status table logic and the parser construction into two private modules, keep this module as the CLI entry that re-exports every moved name, and lower its baseline entry (`REQ-005`, `REQ-007`; Plan phase 2).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: running `module_nodes.py extract` to create `tools/_workitem_status_table.py` and `tools/_workitem_stage_parser.py` from this file, the re-export imports, and a zero-argument `build_parser` wrapper here.
- Out of scope: any subcommand behavior, exit code, or the `git mv` logic.

## Assumptions
- Verified on 2026-11-06 (Step 3a): the file is 57,146 B; clusters include `update_execution_status` (about 146 lines), `build_parser` (about 208 lines), `parse_execution_status_rows`, `parse_execution_status_table`, and the `build_table_*` helpers. Importers: `tools/close_procedures_batch.py` (`MoveResult`, `move_to_done`, `parse_execution_status_rows`, `update_execution_status`), `tools/plan_dependency_order.py` (`parse_execution_status_rows`), `tests/tools/test_manage_workitem_stage.py` (including the private names `_batch_prefix`, `_discover_batch`, `_find_remote_conflict`, `_run_with_lock_retry`, and `build_parser`, `cmd_close_batch`, `cmd_close_implementation`, `main`), `tests/tools/test_manage_workitem_stage_new.py` (`EXECUTION_STATUS_HEADING`, `build_parser`, `cmd_*`), and `tools/close_procedure.sh`, which runs `manage_workitem_stage.py close-implementation` by path. The tests call `build_parser()` with no argument.
- Plan correction (2026-11-06): the entry module keeps a zero-argument `build_parser` that calls the parser module's builder with its handlers; every name above stays importable from this module.
- Sequencing: this Plan lands last among the `tools/` Plans; the procedures of `toolcommon001` and `toolwrite001` (archived with their procedures generated) are expected to have executed first, because they edit `run_validation_gates.py` and `manage_workitem_stage.py` before this Plan moves code from them.
- The `toolwrite001` procedure for this file (atomic write inside the status update function, bootstrap) is expected to have landed, so the moved code already calls the shared atomic write helper.
- Exact cluster boundaries are decided at execution with `module_nodes.py measure` (Plan UNK-02); a helper needed by both clusters moves with the status table module. radon grades of the moved functions (`update_execution_status` D 30, `cmd_close_batch` D 21) MUST NOT rise: the move is verbatim.
- Correction (code-implementation Step 3b, 2026-11-06): `build_parser` does not reference any `cmd_*` handler (the entry module's `main` dispatches on `args.subcommand`), so the parser module keeps a zero-argument `build_parser()` and the entry module imports and re-exports it directly; no handler argument and no wrapper are needed. `_valid_status_type` moved with `build_parser`, and `_normalize_status` lives in the status-table module that the parser imports.

## Design decisions
- Dependency direction: the entry module imports `_workitem_status_table` (new) and `_workitem_stage_parser` (new); neither imports the entry module (the parser receives handlers as an argument).
- Keep `main`, the `cmd_*` handlers, `move_to_done`, locking, and the `git` code here.

## Alternatives considered
- Move every cluster out: rejected, exceeds the Plan's "reduce" criterion.

## Implementation
### Target file
`tools/manage_workitem_stage.py`

### Procedure
1. Run `uv run python tools/module_nodes.py measure tools/manage_workitem_stage.py` and list the dependencies of `update_execution_status` and `build_parser` (`rg`) to fix the two move sets.
2. `module_nodes.py extract --src tools/manage_workitem_stage.py --dest tools/_workitem_status_table.py --name ...` for the status-table functions (and their private helpers and constants by `--range`), then the same for `tools/_workitem_stage_parser.py` with `build_parser` (and its `type=` validators).
3. Add the import blocks here for every moved name still used or imported elsewhere; add `def build_parser() -> argparse.ArgumentParser:` here as a thin wrapper that passes the `cmd_*` handlers; mark names kept only for importers with `# noqa: F401 — re-exported for close_procedures_batch, plan_dependency_order, and tests`.
4. Prove each move with `module_nodes.py compare --old-rev HEAD --old-src tools/manage_workitem_stage.py --new-src <new module> ...` and run the tests.

### Method
- `extract` moves exact source ranges; only imports and the wrapper are hand-written.

### Details
- After the move lower this file's baseline entry with `--update-baseline` and review the diff (no entry raised or added, `REQ-007`); run each subcommand (`show`, `list`, `set-step-status` with a copy, `close-plan --stage-only` in a temporary clone is not required) before and after on live data.
- Verify the by-path call: `uv run python tools/manage_workitem_stage.py --help` and a `show` run.

## Compatibility considerations
- Every CLI subcommand, exit code, and import path used by the two importers and the tests is unchanged.

## Security considerations
N/A: verbatim move; no new input.

## Rollback considerations
- This tool moves workflow documents and is used by skills: revert the commit if any subcommand or test regresses; the extract is verbatim.

## Validation plan
- `uv run pytest tests/tools/test_manage_workitem_stage.py tests/tools/test_manage_workitem_stage_new.py tests/tools/test_close_procedures_batch.py tests/tools/test_plan_dependency_order.py -q`, then `uv run pytest tests/tools -q`.
- Before and after on live data: `uv run python tools/manage_workitem_stage.py list --kind plan --status Pending` and `show plan <a real plan>`; compare output.
- `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` (shrinkage reported, exit 0).
- `routing.md` "Adding a new tool" steps 1-3 for the three files, then `uv run python tools/run_validation_gates.py`.

## Completion criteria
- The two new modules exist, this module re-exports every moved name and keeps a zero-argument `build_parser`, `compare` reports identical moved functions, no subcommand or test regresses, no radon grade rises, and the baseline entry is lower.

## Out of Scope
- Behavior changes, the other oversized tools.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Measure and fix the two move sets | Completed | 20261106-121750 | 20261106-121940 | Changed: tools/manage_workitem_stage.py (57287 B -> 39694 B; imports and re-exports the moved names); baseline entry lowered |
| 2 | Extract the status-table and parser clusters and add the re-exports and wrapper | Completed | 20261106-121940 | 20261106-121940 | 99 tests of manage_workitem_stage, close_procedures_batch, plan_dependency_order pass; no test edit needed |
| 3 | Prove with `compare`, run the tests and the live-data comparison | Completed | 20261106-121940 | 20261106-121940 | ruff, mypy, bandit clean; module_nodes compare identical for all moved functions; radon grades unchanged; every subcommand's help and list/show/detect-stale output identical to the pre-split module; by-path --help OK from another cwd; close_procedure.sh syntax OK |
| 4 | Lower the baseline entry and review the diff | Completed | 20261106-121940 | 20261106-121940 | N/A: documentation is another procedure of this Plan |

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
- **Requirement ID**: `REQ-005` (split by responsibility), `REQ-007` (baseline shrinks)
- **Source issue**: issues/20261104-152002_toolsizegate001_apply-size-gate-to-tools.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-110406_toolsizegate001_apply-size-gate-to-tools.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-092637
- **Related target files**: `tools/manage_workitem_stage.py`
