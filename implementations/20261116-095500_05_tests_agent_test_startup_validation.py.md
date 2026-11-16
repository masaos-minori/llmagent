## Goal

Add pipeline tests showing that a timed-out RAG consistency check is stopped, that loop close does not wait for the check, and that an in-time check still reports fatal findings (`REQ-003`, `REQ-004`, `REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new tests in `tests/agent/test_startup_validation.py`.
- Out of scope: production code, the existing tests in the file, and the helper-level hook tests (document `01` companion).

## Assumptions

- Per the Plan's tests-first rule, write these tests before documents `02` and `03` and confirm the stop tests fail on the current code; this document has no code dependency (the fake service defines its own `consistency(stop=...)`), so it can be executed first even though its `seq` is later.
- This Plan is gated (sequencing only) behind `plans/20261115-043850_dbreview005_helper-open-leak.md`.
- This file is a target of its own document because two other rows (`rag_maintenance_service.py` and `startup_validation.py`) name it in `Related Tests`, which makes it ineligible as a companion. It is also a target of Plan `startrev004`, whose procedure is generated later; the two sets of tests are additive.
- The file builds the pipeline through a helper that patches `agent.startup_validation.RagMaintenanceService` with a `MagicMock` and optionally `agent.startup_validation.asyncio.wait_for` (read in Step 3a); the new tests follow that helper's pattern.

## Design decisions

- Use a fake service class whose `consistency(self, stop=None)` blocks on `stop.wait(timeout=...)` until the event is set, then returns a minimal consistent result; monkeypatch `agent.startup_validation.RAG_CONSISTENCY_TIMEOUT_SEC` (new) to a small value instead of patching `asyncio.wait_for`.
- Assert outcomes and elapsed time (lower and generous upper bounds), not internals.

## Alternatives considered

N/A: the Plan fixes the approach (fake service, shortened bound).

## Implementation
### Target file
`tests/agent/test_startup_validation.py`

### Procedure
1. Add a test for the timeout path: with the shortened bound and the blocking fake, `check_services()` records the existing `rag_consistency` warning, the event passed to the fake is set, and the fake returns without waiting for its natural duration.
2. Add a loop-close test: run the pipeline inside `asyncio.run` and assert the total time stays well below the fake's natural duration, which shows the executor thread was released.
3. Add an in-time test: a fake that returns a consistency result with a fatal finding yields a pipeline fatal for `rag_consistency` and never sets the event.
4. Confirm tests 1 and 2 fail on the current code (the fake is never signaled) and pass after documents `02` and `03`.

### Method
- Reuse the file's `_run_check_services`-style helper and `_rag_outcomes`; add the constant patch with `monkeypatch`/`patch` on the pipeline module.
- Comments in English. Keep every assertion's bound lower-bound-only for timing where possible to avoid flakiness on a loaded host.

### Details
- Use `threading.Event` in the fake (the pipeline passes a `threading.Event`); do not use an `asyncio.Event`.
- Do not touch the real `rag` database; the service is faked.

## Compatibility considerations

N/A: tests only; existing tests are unchanged.

## Security considerations

N/A: no production code and no secrets.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_startup_validation.py tests/agent/test_startup.py -q`; the stop tests fail before documents `02` and `03` and pass after.
- `uv run ruff check tests/agent/test_startup_validation.py` and `uv run ruff format --check` on it.

## Completion criteria

- The timeout, loop-close and in-time tests exist; the first two fail on the pre-change code and all pass after the change (`REQ-003`, `REQ-004`, `REQ-005`, AC-3 to AC-6).

## Out of Scope

- Production code, helper tests, documentation, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the timeout, loop-close and in-time pipeline tests and confirm the stop tests fail on the current code | Pending | — | — | Gated: plans/20261115-043850_dbreview005_helper-open-leak.md phase all - Plan is gated as a whole (shared `scripts/db/helper.py`); sequencing only |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the test file | Pending | — | — | Gated: plans/20261115-043850_dbreview005_helper-open-leak.md phase all - Plan is gated as a whole (shared `scripts/db/helper.py`); sequencing only |

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
- **Requirement ID**: `REQ-003` (timeout stops the check), `REQ-004` (loop close does not wait), `REQ-005` (in-time behavior kept)
- **Source issue**: issues/20261115-214906_startrev006_rag-check-timeout-executor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-220927_startrev006_rag-check-timeout-executor.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095500
- **Related target files**: `tests/agent/test_startup_validation.py`
