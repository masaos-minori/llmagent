## Goal

Let `RagMaintenanceService.consistency` accept an optional stop event and install the stop hook when given one, with unchanged behavior without it (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `consistency` method in `scripts/agent/services/rag_maintenance_service.py`.
- Out of scope: `check_rag_consistency` and `scripts/db/rag_consistency.py` (not modified), the other callers' behavior, and the pipeline (document `03`).

## Assumptions

- Execute after document `01` of this Plan: `SQLiteHelper.interrupt_when` must exist.
- This Plan is gated (sequencing only) behind `plans/20261115-043850_dbreview005_helper-open-leak.md`; that Plan does not touch this file.
- `consistency` has two callers, `StartupValidationPipeline.check_services` and `cmd_session._rag_consistency` (re-checked with `rg`); the new keyword is optional, so `cmd_session.py` is unchanged.
- Each stage of `check_rag_consistency` catches `sqlite3.Error` and records a diagnostic, so an aborted statement surfaces as that error class and the context manager still closes the connection (read in Step 3a).
- Test coverage for this method comes from the pipeline tests in document `05` (`tests/agent/test_startup_validation.py` is a target of its own document because two Plan rows name it) and the helper tests in document `01`; this file has no test document of its own.

## Design decisions

- Add the keyword-only parameter `stop: threading.Event | None = None`; when it is not `None`, call `db.interrupt_when(stop)` inside the `with` block before `check_rag_consistency(db)`.
- Return the same `RagConsistencyResult` as today; nothing about the result mapping changes.

## Alternatives considered

N/A: the Plan fixes the placement (connection level, used by this service).

## Implementation
### Target file
`scripts/agent/services/rag_maintenance_service.py`

### Procedure
1. Add `import threading` (sorted per ruff `I`) and the keyword-only parameter `stop` to `consistency`.
2. Inside `with SQLiteHelper("rag").open() as db:`, call `db.interrupt_when(stop)` when `stop` is not `None`, then run `check_rag_consistency(db)` as before.
3. Extend the docstring: `stop`, when set, aborts the running statements; aborted stages are recorded by the check as diagnostics.

### Method
- Keep the `with` block and the result construction exactly as they are; only the optional hook line and the signature change.

### Details
- Do not wrap the call in a new `try/except`; the stage-level handling in `check_rag_consistency` is the intended boundary.

## Compatibility considerations

- A call without arguments behaves exactly as before; `cmd_session._rag_consistency` is unchanged.

## Security considerations

- N/A: the method opens the same database read-only path as today and adds no input.

## Rollback considerations

- Revert the commit; document `03` passes the keyword and must be reverted with it.

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py -q` and any test that calls `consistency()` (for example `tests/agent/test_cmd_session*.py` if present, found with `rg 'consistency\(' tests/agent`).
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py` and `uv run python tools/generate_reference_table.py --check`.

## Completion criteria

- `consistency()` without arguments behaves as before; with `stop` it installs the hook before running the check (`REQ-002`, AC-2).

## Out of Scope

- Pipeline changes, helper changes, documentation, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the optional `stop` keyword to `consistency` and install the hook | Completed | 20261116 | 20261116 | Added `import threading` + keyword-only `stop`; hook installed inside `with` block only when `stop is not None`. Mock smoke check confirms 0 calls without stop, 1 call with stop |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261116 | 20261116 | ruff/mypy/lint-imports/check_module_size/generate_reference_table --check all pass; behavior smoke check passes |

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
- **Requirement ID**: `REQ-002` (optional stop event on `consistency`)
- **Source issue**: issues/20261115-214906_startrev006_rag-check-timeout-executor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220927_startrev006_rag-check-timeout-executor.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095500
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`
