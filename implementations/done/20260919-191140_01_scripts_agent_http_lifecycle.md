## Goal

Delegate `shutdown_all()` to `ShutdownCoordinator.shutdown_all()`, move `_absorb_sigint_during_shutdown`, replace hardcoded `10.0` literal with `HEALTH_RECHECK_INTERVAL_SEC` import, delegate health check to `HealthChecker.verify_running_async()`, split `_cleanup_server_resources()`, and reduce complexity below 150 lines.

## Scope

- **In-Scope**: Delegating `shutdown_all()`, moving `_absorb_sigint_during_shutdown`, replacing hardcoded literal, delegating health check, splitting `_cleanup_server_resources()`
- **Out-of-Scope**: Changes to `ShutdownCoordinator.shutdown_all()` (handled in companion procedure), fixing circular imports in `HealthChecker` (handled in companion procedure), deleting dead code (handled in separate procedure)

## Assumptions

- `ShutdownCoordinator.shutdown_all()` already owns `_http_procs` mutation (verified in companion procedure)
- `McpServerConfig` has no `health_url` field — only `url` — so delegating health checks requires explicit URL construction: `cfg.url.rstrip("/") + "/health"`
- The rate-limiting wrapper logic (10-second interval) should be kept but delegated to `HealthChecker.verify_running_async()`

## Design decisions

- Make `HttpServerLifecycleManager.shutdown_all()` a thin delegating wrapper — keep callable for backward compat, but delegate internally
- Move `_absorb_sigint_during_shutdown` to `ShutdownCoordinator` only; delete duplicate from `HttpServerLifecycleManager`
- Replace hardcoded `10.0` literal with module-level constant reference from `http_lifecycle_health_checker`
- Delegate HTTP request to `HealthChecker.verify_running_async()`, passing URL explicitly
- Split `_cleanup_server_resources()` into `_read_stderr_for_cleanup()` and `_clear_server_tracking_data()`

## Alternatives considered

- Removing `HttpServerLifecycleManager.shutdown_all()` entirely instead of making it a delegating wrapper — rejected because backward compatibility requires keeping the method callable
- Extracting timeout to a shared constants module instead of passing as parameter — rejected because the plan specifies passing as parameter to `HealthChecker.compute_health_check_timeout()`

## Implementation

### Target file

scripts/agent/http_lifecycle.py

### Procedure

Implement five distinct changes: delegate shutdown_all(), move _absorb_sigint_during_shutdown, replace hardcoded literal, delegate health check, split _cleanup_server_resources().

### Method

#### Step 1: Delegate shutdown_all()

Replace the body of `HttpServerLifecycleManager.shutdown_all()` with a delegation call to `ShutdownCoordinator.shutdown_all()`. Keep the method signature unchanged for backward compatibility.

```python
def shutdown_all(self):
    """Shut down all managed servers."""
    return self._shutdown_coordinator.shutdown_all()
```

#### Step 2: Move _absorb_sigint_during_shutdown

Delete `_absorb_sigint_during_shutdown` from `HttpServerLifecycleManager` and ensure it exists only in `ShutdownCoordinator`. If it doesn't exist in `ShutdownCoordinator`, add it there as a static method.

#### Step 3: Replace hardcoded literal

Replace the hardcoded `10.0` literal in `verify_running_async()` with a reference to `HEALTH_RECHECK_INTERVAL_SEC` from `http_lifecycle_health_checker` module level.

```python
from agent.http_lifecycle_health_checker import HEALTH_RECHECK_INTERVAL_SEC

# In verify_running_async():
interval = HEALTH_RECHECK_INTERVAL_SEC  # was: interval = 10.0
```

#### Step 4: Delegate health check

Replace the inline HTTP request in `verify_running_async()` with a delegation to `HealthChecker.verify_running_async()`, passing `url=cfg.url.rstrip("/") + "/health"` explicitly.

```python
# Before: inline HTTP request
# After:
result = HealthChecker.verify_running_async(url=cfg.url.rstrip("/") + "/health")
```

#### Step 5: Split _cleanup_server_resources()

Separate into two methods:
- `_read_stderr_for_cleanup()` — returns stderr content
- `_clear_server_tracking_data()` — removes health check timestamps, stderr file handles, paths

Call them separately where needed.

### Details

The full refactored `shutdown_all()` method:

```python
def shutdown_all(self):
    """Shut down all managed servers.
    
    Delegates to ShutdownCoordinator.shutdown_all() after verifying
    _http_procs mutation parity (REQ-001).
    """
    return self._shutdown_coordinator.shutdown_all()
```

The refactored `verify_running_async()` method:

```python
async def verify_running_async(self, cfg: McpServerConfig) -> bool:
    """Verify server is running using HealthChecker delegation."""
    url = cfg.url.rstrip("/") + "/health"
    try:
        result = await HealthChecker.verify_running_async(url=url)
        return result
    except Exception as e:
        logger.error(f"Health check failed for {cfg.url}: {e}")
        return False
```

## Compatibility considerations

- Public API (`shutdown_all()`) signature unchanged — backward compatible
- Making `shutdown_all()` a delegating wrapper preserves external contract while changing internal behavior
- Replacing hardcoded literal with constant reference is transparent to callers
- Delegating health check preserves same semantics — just moves implementation detail

## Security considerations

- No security-relevant behavior changes — same validation and permission checks as before
- Parameter passing preserved exactly — no new attack surface from delegation

## Rollback considerations

- If delegation breaks behavior, revert to original monolithic `shutdown_all()` body
- Keep extracted methods private — no external contract to maintain during rollback
- If `_absorb_sigint_during_shutdown` deletion causes issues, restore it temporarily

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| HttpServerLifecycleManager.shutdown_all() | Integration: verify delegation works correctly | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v -k shutdown` | Delegation preserves cleanup behavior |
| verify_running_async() | Unit: verify HEALTH_RECHECK_INTERVAL_SEC usage | `uv run pytest tests/agent/ -v -k health` | Tests pass with constant reference |
| _cleanup_server_resources() split | Integration: verify both methods work correctly | `uv run pytest tests/agent/test_http_lifecycle_integration.py -v -k cleanup` | Both methods produce same result as original |
| Full test suite | Regression — all http_lifecycle tests | `uv run pytest tests/agent/ -q --ignore=tests/integration/` | All tests pass |
| Type checking | Static analysis | `uv run mypy scripts/agent/http_lifecycle*.py` | Clean |
| Linting | Style check | `uv run ruff check scripts/agent/http_lifecycle*.py` | Clean |

## Completion criteria

- `HttpServerLifecycleManager.shutdown_all()` delegates to `ShutdownCoordinator.shutdown_all()`
- `_absorb_sigint_during_shutdown` exists only in `ShutdownCoordinator`
- `verify_running_async()` uses `HEALTH_RECHECK_INTERVAL_SEC` from module level
- `verify_running_async()` delegates to `HealthChecker.verify_running_async()` with explicit URL
- `_cleanup_server_resources()` split into two separate methods
- Complexity reduced below 150 lines
- All existing tests pass
- No behavioral regression — same inputs produce same outputs
- Type checker passes on modified file
- Linter passes on modified file

## Out of scope

- Adding `_http_procs` mutation to `ShutdownCoordinator.shutdown_all()` (companion procedure)
- Fixing circular imports in `HealthChecker.compute_health_check_timeout()` (companion procedure)
- Deleting `ProcessSnapshotProvider` (separate procedure)
- Deciding whether `ProcessTerminator.terminate_with_timeout()` should return boolean (UNK-02)
- Making health-recheck interval configurable via `McpServerConfig` (out of scope per plan)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-003, REQ-004, REQ-006, REQ-007, REQ-008
- **Source issue**: issues/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-120000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-191140
- **Related target files**: scripts/agent/http_lifecycle.py
