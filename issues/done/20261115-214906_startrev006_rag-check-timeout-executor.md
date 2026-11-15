# The startup RAG consistency timeout does not stop the check and delays process exit

## Priority
Medium

## Summary
`StartupValidationPipeline.check_services` runs `RagMaintenanceService().consistency()` in the default thread executor and bounds it with `asyncio.wait_for`. On a timeout the awaiting coroutine is released, but the worker thread keeps running and keeps its `rag` database connection open. The warning says startup continues, yet `asyncio.run` waits for the default executor to finish when the loop closes, so the bound is not a real bound on how long the process lives. Make the check cancellable or bound its own run time.

## Background
- Found by an adversarial review of the agent startup path (`scripts/agent`) at commit `490fccc50`.
- Evidence (Explicit in code): `check_services` wraps `loop.run_in_executor(None, lambda: RagMaintenanceService().consistency())` in `asyncio.wait_for(..., timeout=...)` and handles `TimeoutError` with a warning.
- Evidence (Explicit in code): `RagMaintenanceService.consistency` opens `SQLiteHelper("rag")` and runs `check_rag_consistency`; it has no deadline, cancellation check or interrupt hook.
- Evidence (Operationally observed): a throwaway reproduction ran a 3 s blocking call in the default executor under a 0.2 s `wait_for`; the timeout was raised at 0.2 s and `asyncio.run` returned only at 3.0 s, when the worker finished. This shows the generic mechanism; the real duration of `consistency()` on a large database is not measured.
- Related, not overlapping: `plans/20261115-050112_dbreview006_maintenance-error-semantics.md` changes the maintenance error contract in `db.maintenance`, not this timeout.

## Problem
After a timeout the agent starts, the operator uses it, and on exit `asyncio.run` blocks until the consistency check completes (bounded only by the runtime's own executor join limit). A slow check therefore shows up as a hang at shutdown, long after the "timed out after the bound" message, and the thread holds a database connection for that whole time. The user-visible message and the actual behavior disagree.

## Reason for Change
The check exists to catch corruption early; when it is slow it is exactly the case where the user waits most. The fix is small and local. Medium because the effect is delay and a lingering connection, not data corruption.

## Implementation Intent
Give the consistency run its own bound that stops the work, not only the wait for it: for example a deadline or interrupt checked inside the check, or a progress hook that the timeout can set. Keep the result semantics (fatal findings fatal, timeout a warning with startup continuing). Do not change what the check verifies.

## Target Files or Areas
- scripts/agent/startup_validation.py (`StartupValidationPipeline.check_services`, RAG step)
- scripts/agent/services/rag_maintenance_service.py (`RagMaintenanceService.consistency`)
- scripts/rag (consistency check code reached through `check_rag_consistency`; location to confirm)
- tests/agent/shared/test_startup_validation_pipeline.py

## Required Changes
- Add a cooperative stop (deadline or cancel flag) to the consistency run and set it when the startup bound expires.
- Make the stopped run close its database connection and return promptly.
- Keep the warning text accurate about what happened to the check.
- Add a test with a fake check that blocks until stopped: after the bound the pipeline reports the warning, the fake sees the stop signal, and the event loop closes without waiting for the original duration.

## Constraints
- Findings with fatal severity MUST remain fatal; the timeout MUST remain a warning only.
- The check MUST NOT write to the `rag` database.
- Do not run the check on the event loop thread.

## Acceptance Criteria
- After the startup bound expires the consistency run stops within a short, tested interval and releases its connection.
- Closing the event loop after a timed-out check does not wait for the check's natural duration.
- A check that finishes in time behaves as before, including fatal findings.
- `uv run pytest tests/agent/shared/test_startup_validation_pipeline.py` passes with the new cases.
- `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/` and `PYTHONPATH=scripts uv run lint-imports` pass.

## Testing Expectations
Unit test with a blocking fake that honors the stop signal; assert loop shutdown time. A regression run of the RAG consistency tests. No test needs a large real database.

## Documentation Impact
Update the startup validation design text for the RAG step: the timeout stops the check and startup continues with RAG consistency unverified. No values.

## Out of Scope
- Changing what the consistency check verifies or its severity classification.
- The check's performance on large databases.
- Making other executor-backed startup calls cancellable.

## Dependencies
- `issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md` — related: abandoning this wait on a shutdown request needs the same cooperative stop; implement the stop mechanism once and reuse it.

## Unresolved Questions
- How long does `consistency()` take on the production-sized `rag` database? This sets how visible the exit delay is. (Needs confirmation)
- Where is the cooperative stop best placed in the consistency check code under `scripts/rag`? (Needs confirmation)

## AI Implementation Instruction
Keep changes minimal and confined to the consistency path. Do not change what the check verifies. Do not use the production database in tests.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261115-214906
- **Related target files**: scripts/agent/startup_validation.py, scripts/agent/services/rag_maintenance_service.py, tests/agent/shared/test_startup_validation_pipeline.py
