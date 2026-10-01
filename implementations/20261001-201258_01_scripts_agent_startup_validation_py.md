# Implementation Procedure: startup_validation.py — move blocking sync I/O out of async event loop

## Goal

Move the synchronous blocking I/O call `RagMaintenanceService().consistency()` out of the asyncio event loop by scheduling it via `loop.run_in_executor()`, eliminating the event-loop-blocking pattern while preserving pipeline semantics. Implements `REQ-001` (short purpose: schedule `consistency()` via executor), `REQ-002` (short purpose: preserve exception handling around executor-wrapped call).

## Scope

- **In scope**: Wrapping `RagMaintenanceService().consistency()` in `StartupValidationPipeline.check_services()` with `run_in_executor`; verifying no other calls in `check_services()` perform blocking I/O.
- **Out of scope**: Changing which checks run or their severity classification; refactoring non-startup callers of `RagMaintenanceService.consistency()` (e.g. `cmd_session.py`).

## Assumptions

- The executor's default thread pool (`None` argument to `run_in_executor`) is sufficient for this use case.
- No subclass overrides of `StartupValidationPipeline.check_services()` depend on the current synchronous execution order.
- The broad `except Exception` handler in `check_services()` catches exceptions raised from `run_in_executor` futures (but NOT `asyncio.CancelledError` since Python 3.8+ — see Security considerations).

## Design decisions

- **Schedule the entire `RagMaintenanceService().consistency()` call (including instance creation) inside the executor lambda**, avoiding any serialization issues with instance construction crossing the executor boundary.
- **Add `import asyncio`** at the top of the file (currently not imported; only `TYPE_CHECKING` is present).
- **Do NOT add `except asyncio.CancelledError`** expecting it to be caught by `except Exception` — `CancelledError` subclasses `BaseException` in Python 3.8+, so `except Exception` does NOT catch it. If shutdown-cancellation semantics matter, handle it explicitly; otherwise rely on default propagation.

## Alternatives considered

- **Restructure so the blocking call happens outside the coroutine**: would require changing the function signature or control flow significantly. Rejected in favor of the simpler `run_in_executor` approach.
- **Use `asyncio.to_thread()` instead of `loop.run_in_executor()`**: available in Python 3.9+, but `loop.run_in_executor(None, ...)` is equivalent and more explicit about using the default thread pool. Retained for clarity.

## Implementation

### Target file

`scripts/agent/startup_validation.py`

### Procedure

1. Read `scripts/agent/startup_validation.py` and confirm the exact location of the `RagMaintenanceService().consistency()` call (line ~128) and that `import asyncio` is not currently present. Confirm via `scripts/agent/services/security_audit.py` and `scripts/agent/services/routing_drift.py` that the other synchronous calls do not block.
2. Add `import asyncio` at the top of `scripts/agent/startup_validation.py` (after existing imports).
3. Replace the direct call `rag_check = RagMaintenanceService().consistency()` with:
   ```python
   loop = asyncio.get_running_loop()
   rag_check = await loop.run_in_executor(
       None,
       lambda: RagMaintenanceService().consistency(),
   )
   ```
4. Verify no new lint errors (especially unused-import) by running `ruff check` on the file.

### Method

- Keep the change minimal: only modify the RAG consistency call site and add the import. Do not alter any other method, class, or module-level construct.
- After modification, verify the file still parses correctly (no dangling references).
- Run `ruff check` to confirm no new lint errors.

### Details

- Current code at line 128:
  ```python
  rag_check = RagMaintenanceService().consistency()
  ```
- New code should be:
  ```python
  loop = asyncio.get_running_loop()
  rag_check = await loop.run_in_executor(
      None,
      lambda: RagMaintenanceService().consistency(),
  )
  ```
- The `None` argument to `run_in_executor` uses the default `ThreadPoolExecutor`, which is sufficient for this single concurrent task.
- The lambda closure ensures the entire `RagMaintenanceService().consistency()` call (including instance creation) happens inside the executor thread pool, avoiding any serialization issues.

## Compatibility considerations

- Startup validation outcomes are unchanged: same OK/FATAL/WARNING/SKIPPED results (AC-002 / REQ-002).
- Existing discovery tests (`tests/agent/shared/test_startup_validation_pipeline.py`) must continue to pass.
- No public interface changes — `check_services()` returns the same `StartupValidationResult`.

## Security considerations

- `asyncio.CancelledError` subclasses `BaseException` in Python 3.8+, so `except Exception` does NOT catch it. If shutdown-cancellation semantics matter during executor wait, handle `CancelledError` explicitly at the await point. Otherwise rely on default propagation (do NOT add `except Exception` expecting it to cover cancellation).
- N/A: no secrets, credentials, or sensitive data are introduced.

## Rollback considerations

- Single-file change; reverting the commit restores the original synchronous call with no data migration or config change. `deploy.sh` impact is limited to the startup pipeline; no deploy/config change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_validation.py` | Lint check | `ruff check scripts/agent/startup_validation.py` | Clean (no errors) |
| `scripts/agent/startup_validation.py` | Type check | `mypy scripts/agent/startup_validation.py` | Clean (no type errors) |
| `tests/agent/shared/test_startup_validation_pipeline.py` | Regression test | `pytest tests/agent/shared/test_startup_validation_pipeline.py` | All tests pass |

## Completion criteria

- `consistency()` (and other confirmed-blocking calls) no longer run on the event loop thread (AC-001 / REQ-001).
- Startup validation outcomes are unchanged (same OK/FATAL/WARNING/SKIPPED results) (AC-002 / REQ-002).
- `ruff` / `mypy` clean on the file (AC-004 / REQ-004).

## Out of scope

- Any refactor of non-startup callers of `RagMaintenanceService.consistency()`.
- Changing which checks run or their severity classification.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Preparation / Verification — confirm no other blocking calls exist | In Progress | 20261001-201349 | — | REQ-001, REQ-002 |
| 2 | Phase 2: Core Logic Implementation — add `import asyncio`; wrap `consistency()` with `run_in_executor` | Pending | — | — | REQ-001, REQ-002 |
| 3 | Phase 3: Deployment & Verification — ruff/mypy/pytest | Pending | — | — | REQ-002, REQ-004 |

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
- **Requirement ID**: `REQ-001` — schedule `consistency()` via executor; `REQ-002` — preserve exception handling around executor-wrapped call
- **Source issue**: issues/done/20260930-161945_async001_startup_validation_blocking_sync_io_in_async_context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-094120_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-201258
- **Related target files**: scripts/agent/startup_validation.py