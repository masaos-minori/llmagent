# Startup validation pipeline runs synchronous blocking I/O inside an async method

## Priority
Medium

## Summary
`StartupValidationPipeline.check_services()` (`scripts/agent/startup_validation.py`) is declared `async def` but invokes several fully synchronous, potentially blocking operations directly -- most notably `RagMaintenanceService().consistency()`, which opens `rag.sqlite` and runs a consistency read via `SQLiteHelper`. These block the asyncio event loop. Run such work off the loop (e.g. `loop.run_in_executor`) or move it out of the async path to comply with the project's Pythonic safety constraints.

## Background
`check_services()` is the single async entry point for the startup service-validation pipeline (security audit, MCP auth, readiness, tool discovery, routing drift/safety tiers, RAG consistency). Tool discovery is genuinely async (`await McpToolDiscoveryService(ctx).discover_all()`); the other checks are synchronous functions called without awaiting.

## Problem
`RagMaintenanceService.consistency()` opens and reads `rag.sqlite` synchronously (see `RagMaintenanceService.consistency()` / `SQLiteHelper.open()`). Calling it directly inside the `async def check_services()` blocks the event loop for the duration of the DB read. Per `skills/DESIGN.md` Pythonic safety constraints, `async def` functions must not introduce blocking I/O (`time.sleep()`, sync file/network/DB calls) without an executor boundary.

## Reason for Change
Although startup runs before the REPL input loop (so there is little concurrent work to starve today), the pattern violates an explicit project constraint and is trivially copyable into the hot turn-execution path where blocking the loop is genuinely harmful.

## Implementation Intent
Identify every blocking synchronous call within `check_services()` (RAG consistency read, and confirm whether `audit_security_defaults()`, `check_routing_drift()`, `check_routing_safety_tiers()` perform blocking I/O). For genuine blocking work, schedule it via `asyncio.get_running_loop().run_in_executor(...)` or restructure so the blocking call happens outside the coroutine. Do not change what is validated -- only how/where the blocking work runs.

## Target Files or Areas
- `scripts/agent/startup_validation.py` (`check_services()`)
- `scripts/agent/services/rag_maintenance_service.py` (`consistency()`)
- Potentially `scripts/agent/services/security_audit.py`, `scripts/agent/services/routing_drift.py` (confirm whether they block)

## Required Changes
- Add an executor boundary (`run_in_executor`) around `RagMaintenanceService().consistency()` (and any other confirmed blocking call) inside `check_services()`.
- Do not alter the pipeline's ordering, fatal/warning semantics, or outcomes.

## Constraints
- Must remain fail-fast correct: a RAG check failure must keep its existing skipped/warning treatment.
- Executor changes must not introduce unhandled exceptions that escape the existing broad handlers.

## Acceptance Criteria
- `consistency()` (and other confirmed-blocking calls) no longer run on the event loop thread.
- Startup validation outcomes are unchanged (same OK/FATAL/WARNING/SKIPPED results).
- `ruff` / `mypy` clean.

## Testing Expectations
- Unit test stubbing `SQLiteHelper`/`consistency()` to run in a thread and asserting the pipeline still classifies consistent/inconsistent results identically.
- Confirm no `CancelledError` leaks from the executor path.

## Documentation Impact
If `docs/` records the startup pipeline as asynchronous, note which steps are offloaded to an executor.

## Out of Scope
- Changing which checks run or their severity classification.
- Refactoring non-startup callers of `RagMaintenanceService.consistency()` (e.g. `cmd_session.py`).

## Dependencies
N/A: none.

## Unresolved Questions
Whether `audit_security_defaults()`, `check_routing_drift()`, and `check_routing_safety_tiers()` perform blocking I/O -- they appear config/static-analysis bound; confirm before scheduling all three.

## AI Implementation Instruction
Do not change pipeline semantics. Only move confirmed-blocking synchronous calls off the event loop via run_in_executor. First confirm which helpers actually block before changing them.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-161945
- **Related target files**: scripts/agent/startup_validation.py, scripts/agent/services/rag_maintenance_service.py
