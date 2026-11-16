## Goal

In the RAG step of `StartupValidationPipeline.check_services`, create a stop event per run, pass it to `consistency`, set it when the startup bound expires, and name the bound as a module constant (`REQ-003`: bound expiry stops the check; `REQ-004`: loop close does not wait for the check; `REQ-005`: in-time behavior unchanged and a named constant).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the RAG consistency step of `check_services` in `scripts/agent/startup_validation.py`.
- Out of scope: the readiness and discovery steps (Plan `startrev005`), shutdown-signal handling (Plan `startrev004`, which reuses the event added here), and what the consistency check verifies.

## Assumptions

- Execute after documents `01` and `02` of this Plan (the hook and the `stop` keyword must exist), and after the Plan `startrev005` procedures: that Plan edits the head of `check_services`, this change edits the RAG step; no line is shared (overlap judged compatible, sequencing dependency).
- This Plan is gated (sequencing only) behind `plans/20261115-043850_dbreview005_helper-open-leak.md`.
- `asyncio.wait_for` cancels the executor future on timeout but the worker thread continues; `asyncio.run` then waits for the default executor at loop close, which is the exit delay this change removes (read in Step 3a).
- Existing tests patch `agent.startup_validation.asyncio.wait_for` with a `side_effect` and use `MagicMock` services, so passing an extra keyword to `consistency` does not break them (re-read in `tests/agent/test_startup_validation.py`).
- Tests for this behavior live in document `05` (`tests/agent/test_startup_validation.py` is named by two Plan rows, so it is a target of its own document, not a companion).

## Design decisions

- Create `stop = threading.Event()` (new import `threading`) right before the RAG `try`, pass it as `RagMaintenanceService().consistency(stop=stop)` in the executor lambda, and call `stop.set()` as the first statement of the `except TimeoutError` handler, before the warning is recorded.
- Replace the literal `30.0` (and the `30s` text in the timeout log and warning) by a module constant `RAG_CONSISTENCY_TIMEOUT_SEC` (new) so tests can shorten it; the warning text still names the bound.

## Alternatives considered

- Running the check in its own thread or subprocess: rejected in the Plan (the thread still cannot be stopped; a subprocess is disproportionate).

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
1. Add `import threading` and the module constant `RAG_CONSISTENCY_TIMEOUT_SEC` (new) of type `float`, with the current value, near the other module-level names.
2. In the RAG step, create the event, change the lambda to call `consistency(stop=stop)`, and use `RAG_CONSISTENCY_TIMEOUT_SEC` (new) in `asyncio.wait_for(..., timeout=...)`.
3. In `except TimeoutError`, call `stop.set()` first; build the log and warning text from the constant instead of the literal `30s`, keeping the existing wording otherwise.
4. Leave the generic `except Exception` branch and the severity routing of findings unchanged. Set the event there too only if the Plan's tests show a stuck thread on that path; otherwise do not change it.

### Method
- Keep `check_services` free of new branches beyond the one `stop.set()` line; it is radon C (17) and must not grow.
- Messages keep the "startup continues with RAG consistency unverified" meaning.

### Details
- A consistency run that finishes in time never sets the event, so fatal findings still become pipeline fatals exactly as today.
- Do not create the event inside the lambda; it must be shared with the handler.

## Compatibility considerations

- A timeout still produces the existing warning and startup continues; the only observable change is that the worker stops and the process no longer waits for the check at exit. Tests that assert the timeout message may need the text built from the constant to stay equal (the wording is preserved).

## Security considerations

- N/A: no new input; the check stays read-only and fail-closed downstream.

## Rollback considerations

- Revert the commit; document `02`'s keyword is optional and harmless if left in place.

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py tests/agent/shared/test_startup_validation_pipeline.py -q`; the stop tests of document `05` fail on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- On timeout the event is set, the existing warning is reported, and the consistency run stops within a short tested interval with its connection closed (`REQ-003`, AC-3); loop close does not wait for the check's natural duration (`REQ-004`, AC-4).
- An in-time check yields the same outcomes as before and the bound is a named module constant (`REQ-005`, AC-5).

## Out of Scope

- Readiness and discovery steps, shutdown-signal handling, the check's own logic, documentation (document `06`), and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the named bound constant, create and pass the stop event, set it in the `TimeoutError` handler | Pending | — | — | Gated: plans/20261115-043850_dbreview005_helper-open-leak.md phase all - Plan is gated as a whole (shared `scripts/db/helper.py`); sequencing only |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: plans/20261115-043850_dbreview005_helper-open-leak.md phase all - Plan is gated as a whole (shared `scripts/db/helper.py`); sequencing only |

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
- **Requirement ID**: `REQ-003` (timeout stops the check), `REQ-004` (loop close does not wait), `REQ-005` (in-time behavior kept, named bound)
- **Source issue**: issues/20261115-214906_startrev006_rag-check-timeout-executor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220927_startrev006_rag-check-timeout-executor.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095500
- **Related target files**: `scripts/agent/startup_validation.py`
