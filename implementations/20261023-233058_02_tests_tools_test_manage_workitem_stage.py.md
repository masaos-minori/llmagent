## Goal

Add tests for the new `close-batch` subcommand to `tests/tools/test_manage_workitem_stage.py`, mirroring the existing `close-implementation` cases (same `temp_git_repo` fixture, `_commit_file` helper, and `build_parser().parse_args([...])` + `cmd_*` invocation pattern), covering batch discovery, the atomic `Pending` refusal, idempotency, dry-run, and a temp-git integration case that asserts the plan rows are updated. (`REQ-001`, `REQ-002`, `REQ-003`, `REQ-005`, `REQ-007`)

## Scope

- **In-Scope**: append `close-batch` test cases to the existing `tests/tools/test_manage_workitem_stage.py` only — no change to the module under test itself (that is seq 01).
- **Out-of-Scope**: implementing the `close-batch` subcommand, registering the tool in `tools/TOOL_DESCRIPTIONS.md` (seq 03), or referencing it from `skills/code-implementation/workflow.md` (seq 04).

## Assumptions

- The `close-batch` subcommand exposes a discoverable entry point (a `cmd_close_batch(args)` function and a `close-batch` parser branch) that the tests can invoke the same way as `cmd_close_implementation`.
- A batch is identified by a shared timestamp prefix in `implementations/<prefix>_NN_*.md`; the integration fixture writes a synthetic batch plus an owning plan carrying that prefix in its `Implementation Target Files` table.
- The existing `temp_git_repo` fixture (creates `issues/`, `plans/`, `implementations/` with their `done/` subdirs, `git init`, one initial commit) is sufficient for the archive path, since `move_to_done()` requires the destination directory to exist on disk.

## Design decisions

- **Reuse the existing fixture and invocation style.** Each test builds args with `build_parser().parse_args(["close-batch", <batch-id>, ...flags])` and calls the returned command function, asserting on the returned exit code and on the resulting filesystem/git state — exactly as the `close-implementation` cases do.
- **Drive discovery through a real temp repo.** The integration test materializes both the procedures and the owning plan inside `temp_git_repo`, so discovery, the `Pending` pre-check, marking, archiving, and the plan-status update all run against a genuine `git.Repo` and exercise the real `move_to_done()` rename.

## Alternatives considered

- Testing `close-batch` purely via the public `move_to_done()` return value without a temp repo: rejected — the plan requires an integration-style assertion that the plan rows are updated, which needs the full discovery→archive→plan-update flow against a real repo.
- Importing and calling the internal discovery helper directly: rejected — exercising the parsed subcommand end-to-end covers the argparse wiring and dispatch too.

## Implementation

### Target file

`tests/tools/test_manage_workitem_stage.py` (modify)

### Procedure

Append a new section at the end of the file (after the existing `close-implementation` cases) titled `# close-batch:` containing the cases below. Add any imports the new cases need (e.g. the `close-batch` command function) to the existing `from tools.manage_workitem_stage import (...)` block.

### Method

1. **Discovery (`REQ-001`).** Two cases: given a plan path, the command discovers the batch's procedures from that plan's `Implementation Target Files` table; given a bare timestamp prefix, it globs `implementations/<prefix>_*.md`. Assert the discovered set and order match the expected sorted list for each input form.
2. **`Pending` refusal (`REQ-002`).** Materialize a batch where one procedure still has a `Pending` row; assert the command returns a non-zero exit code and that NO file was moved (all procedures still present, no new `done/` entries) and no plan row was changed.
3. **Idempotency (`REQ-007`).** Run `close-batch` once on a clean batch, then again on the same batch id; assert the second run is a no-op or a clear "already closed" refusal (non-zero or a documented no-op message), not a partial re-run, and that no error is raised.
4. **Dry-run (`REQ-005`).** Run `close-batch --dry-run` on a clean batch; assert no file was changed (procedures still present, plan rows unchanged) and that the printed output lists every planned move and edit. Also assert a dry-run of a batch with a `Pending` row reports the block rather than a clean plan.
5. **Integration (`REQ-003`, `REQ-004`).** In a `temp_git_repo` fixture, write 2–3 procedures sharing a prefix (all rows `Completed` or `In Progress`, none `Pending`) and an owning plan whose `Implementation Target Files` table names those procedures; run `close-batch`; assert the procedures were moved into `implementations/done/` and the owning plan's `### Execution Status` rows are now `Completed` with `YYYYMMDD-HHMMSS` timestamps.

### Details

- Reuse the existing string fixtures (`EXECUTION_STATUS_PENDING`, `EXECUTION_STATUS_COMPLETED`) or extend them for multi-row batches; keep the same column structure as `templates/execution-status.md`.
- For the temp-repo integration test, commit each procedure and the plan first (via `_commit_file`) so `move_to_done()`'s auto-commit path is not exercised by uncommitted content unless the test specifically targets it.
- Match the existing assertion style: assert on the returned exit code and on filesystem state (files present/moved) and on the plan content (re-read and check the `Status` cell), not on exact stdout strings except for the dry-run listing.
- Name the cases with `-k` friendly markers matching the plan's Validation plan (`close_batch`, `batch_integration`) so they run via `pytest -k close_batch`.

## Compatibility considerations

Purely additive test cases in an existing test module. No existing test is modified, so no regression to the current `close-implementation`/`move_to_done` coverage. New tests import only symbols that will exist after seq 01 adds the `close-batch` command function.

## Security considerations

N/A: tests exercise archival moves inside a throwaway `temp_git_repo` with no network, credentials, or privilege surface beyond the local `git` operations the existing tests already perform.

## Rollback considerations

Revert the commit that adds these tests, or delete the appended section. Single-file, additive change; `git checkout -- tests/tools/test_manage_workitem_stage.py` fully restores the prior test file.

## Validation plan

- `uv run pytest tests/tools/test_manage_workitem_stage.py -k close_batch` — discovery, `Pending` refusal, idempotency, dry-run all pass.
- `uv run pytest tests/tools/test_manage_workitem_stage.py -k batch_integration` — temp-repo integration passes: plan rows updated, files moved.
- `uv run ruff format` / `ruff check` / `ruff check --fix` clean on the test file.
- `uv run mypy tests/tools/test_manage_workitem_stage.py` clean (matching the module's typing discipline).
- `uv run python tools/check_workitem_structure.py` passes on this generated procedure document.

## Completion criteria

- Discovery (both input forms), `Pending` refusal, idempotency, dry-run, and the temp-repo integration cases are present and pass.
- The integration case asserts both that the procedures are archived and that the owning plan's rows are marked `Completed`.
- `ruff` and `mypy` are clean on the test file.

## Out of Scope

Implementing the `close-batch` subcommand itself, the `tools/TOOL_DESCRIPTIONS.md` registration row, and the `skills/code-implementation/workflow.md` reference pointer.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the `close-batch` subcommand per seq 01 | Pending | — | — | prerequisite for tests |
| 2 | Add `close-batch` tests per Validation plan | Pending | — | — | REQ-001, REQ-002, REQ-003, REQ-005, REQ-007; tests/tools/test_manage_workitem_stage.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | ruff, mypy, pytest -k close_batch |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-005`, `REQ-007`
- **Source issue**: `issues/20261023-173429_workitem001_single-command-to-close-an-executed-implementation-batch-and-its-plan-status.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261023-222901_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-233058
- **Related target files**: `tests/tools/test_manage_workitem_stage.py`
