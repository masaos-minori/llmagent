## Goal

Set the RAG consistency stop event when the services stage is cancelled while the RAG check runs, so the worker thread stops (`REQ-003`: stop on cancellation; `REQ-005`: cancellation test).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: one cancellation handler in the RAG step of `check_services` in `scripts/agent/startup_validation.py` and the companion test file `tests/agent/test_startup_validation.py`.
- Out of scope: the stop mechanism itself (the event, the helper hook and the named bound are added by Plan `startrev006`), the readiness and discovery steps, and the stage race in `scripts/agent/startup.py` (document `01`).

## Assumptions

- Hard ordering: execute after the Plan `startrev006` procedures for `scripts/agent/startup_validation.py` (the stop event and the shortened bound constant exist in the RAG step), `scripts/agent/services/rag_maintenance_service.py` and `scripts/db/helper.py`. The Plan records this as a `Depends on` line for that Plan's phase 2; the dependency tool reports no gate because the Plan is archived, but its procedures may still be unexecuted, so check the code before starting.
- Also execute after the Plan `startrev005` procedures, which edit the head of `check_services`; this change edits only the RAG step.
- `asyncio.wait_for` cancels the awaited executor future on cancellation of the awaiting coroutine, but the worker thread keeps running; the cancellation handler is what stops it (read in Step 3a).
- Test file `tests/agent/test_startup_validation.py` is a companion: it is a Plan row under `tests/`, only the `startup_validation.py` row names it in `Related Tests` (besides itself) in this Plan, and its case is fully specified by the Plan. Plan `startrev006` also adds tests to this file through its own document; the cases are additive.

## Design decisions

- In the RAG step, add an `except asyncio.CancelledError` clause that sets the stop event and re-raises the cancellation; place it before the generic exception clause. The event is the one created for the run by Plan `startrev006`'s change and is also set by the `TimeoutError` handler there.
- Do not swallow the cancellation: the stage race in `startup.py` relies on the cancelled stage finishing with `CancelledError`.

## Alternatives considered

N/A: the Plan fixes the approach (set the existing stop event on cancellation).

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. In the RAG step of `check_services`, add `except asyncio.CancelledError:` that sets the run's stop event and then re-raises, in the same `try` that already handles `TimeoutError` and the generic exception.
2. Keep every other clause, message and the severity routing of findings unchanged.

### Method
- Reuse the stop event variable created for the run by the Plan `startrev006` change; do not create a second event. If that variable is not in scope at the handler, define it before the `try` rather than inside it.
- `CancelledError` derives from `BaseException`, so the generic `except Exception` clause does not catch it; the new clause is required for the event to be set.

### Details
- `check_services` is radon C (17); the added clause must not raise the grade, and the handler body is one statement plus the re-raise.
- No new import: `asyncio` is already imported by the module.

### Companion test files
- `tests/agent/test_startup_validation.py`
  - Procedure: write this first and confirm it fails before the change: run `check_services` as a task with a fake consistency service whose check blocks on the stop event passed to it (a `threading.Event`), wait until the fake has started, cancel the task, and assert `CancelledError` propagates, the stop event is set, and the fake returned. Follow the file's pipeline-building helper and patch the service class as the existing tests do.
  - Validation: `uv run pytest tests/agent/test_startup_validation.py tests/agent/shared/test_startup_validation_pipeline.py -q`.

## Compatibility considerations

- Without cancellation nothing changes. A cancelled services stage now also stops the RAG worker, which only shortens process exit.

## Security considerations

- N/A: no new input; the check stays read-only.

## Rollback considerations

- Revert the commit; the handler is additive and independent of document `01`.

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py tests/agent/shared/test_startup_validation_pipeline.py tests/agent/test_startup.py -q`; the cancellation test fails on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- Cancelling `check_services` while the fake consistency check blocks sets the stop event passed to it and the cancellation still propagates (`REQ-003`, AC-3).
- The cancellation test exists and fails on the pre-change code (`REQ-005`, AC-5).

## Out of Scope

- The stop hook and the named bound, the stage race, documentation (document `05`), and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the cancellation test with a blocking fake and confirm it fails before the change (companion `tests/agent/test_startup_validation.py`) | Pending | — | — | |
| 2 | Add the cancellation handler that sets the stop event and re-raises | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (stop event set on cancellation), `REQ-005` (cancellation test)
- **Source issue**: issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221200_startrev004_startup-ignores-shutdown-signal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095731
- **Related target files**: `scripts/agent/startup_validation.py`, `tests/agent/test_startup_validation.py`
