## Goal

Prevent RAG consistency check from blocking the default executor thread pool during startup validation.

## Scope

- Modify `scripts/agent/startup_validation.py`: add timeout via `asyncio.wait_for` around executor call
- Optionally refactor `RagMaintenanceService.consistency()` to be async (optional, out of scope for this phase)

## Assumptions

- Adding `asyncio.wait_for()` with a reasonable timeout (e.g., 30 seconds) will prevent indefinite blocking
- The current try-except handling in startup_validation.py catches exceptions from the executor call, so timeout exceptions should also be caught
- Making consistency() async is optional — the primary fix is adding a timeout

## Design decisions

- Use `asyncio.wait_for()` with a configurable timeout (default 30 seconds) around the executor call
- Catch `asyncio.TimeoutError` in addition to existing exception handlers
- Keep the existing error handling structure intact

## Alternatives considered

- Making consistency() async — requires changes to its dependencies (database connections), over-engineering for this use case
- Using a separate thread pool with unbounded threads — resource leak risk, doesn't solve the root problem

## Implementation
### Target file
`scripts/agent/startup_validation.py`

### Procedure
Wrap executor call with `asyncio.wait_for()` and timeout in startup_validation.py.

### Method
1. Locate lines 128-145 in `scripts/agent/startup_validation.py` (RAG consistency check)
2. Replace the executor call with `asyncio.wait_for(executor.submit(...), timeout=30)`
3. Update the except clause to catch `asyncio.TimeoutError` in addition to existing exceptions

### Details
```python
# Before (lines 128-145):
try:
    loop.run_in_executor(
        None,
        lambda: RagMaintenanceService().consistency(),
    )
except Exception as e:
    logger.warning(f"RAG consistency check failed: {e}")

# After:
import asyncio

try:
    await asyncio.wait_for(
        loop.run_in_executor(None, lambda: RagMaintenanceService().consistency()),
        timeout=30,  # Configurable timeout to prevent thread pool blocking
    )
except asyncio.TimeoutError:
    logger.error("RAG consistency check timed out after 30s")
except Exception as e:
    logger.warning(f"RAG consistency check failed: {e}")
```

The key change is wrapping the executor call with `asyncio.wait_for()` to enforce a timeout. This prevents indefinite blocking while preserving the existing error handling structure.

## Compatibility considerations

This change is backward-compatible — it adds a timeout that was previously absent. No existing behavior is lost for successful operations. However, slow RAG checks that previously succeeded but took >30s will now fail.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original executor call without timeout if callers depend on indefinite execution. This would restore the previous behavior but reintroduce thread pool blocking risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_validation.py | Unit test — verify timeout enforcement | uv run pytest tests/agent/test_startup_validation.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] RAG consistency check does not block the thread pool (REQ-001)
- [ ] Timeout enforced on the RAG check operation (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to `RagMaintenanceService.consistency()` internal logic
- Changes to the validation pipeline order
- Creating new test file (handled in separate document)

## Implementation outcome

Deviation from procedure: no code change was performed. Origin/master already ships
this fix in commit `10308ed7` — `StartupValidationPipeline.check_services()` wraps
the executor call in `await asyncio.wait_for(loop.run_in_executor(None, lambda:
RagMaintenanceService().consistency()), timeout=30.0)` at lines 129-136, with an
`except TimeoutError:` handler that logs and marks the check skipped (lines 144-148)
rather than blocking the default executor thread pool. The procedure's stated target
(lines 128-145, bare `loop.run_in_executor(...)` under `except Exception` only) does
not match current source, and the Details-block shape differs: origin uses the builtin
`TimeoutError` (not `asyncio.TimeoutError`), logs at WARNING (consistent with the
surrounding checks), and records the skip via `pipeline.add_skipped(...)` where the
draft only logged. REQ-001/REQ-002 behavior is satisfied. Existing regression tests
(`tests/agent/test_startup_validation.py`, `TestRagConsistencyTimeout`) pass (2 passed).
Accepting the upstream implementation and closing the workflow.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Already in origin `10308ed7` (see outcome). |
| 2 | Add or update tests per Validation plan | Done | — | — | `tests/agent/test_startup_validation.py` present, 2 passed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | 2 passed; ruff/bandit clean (no code change). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Skipped | — | — | Out of scope per procedure. |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261004-143006_sv007_blocking_rag_check.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182814_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195207
- **Related target files**: scripts/agent/startup_validation.py
