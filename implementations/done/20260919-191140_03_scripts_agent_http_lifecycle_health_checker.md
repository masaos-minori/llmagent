## Goal

Fix circular import in `HealthChecker.compute_health_check_timeout()` by accepting timeout as a parameter instead of importing it at runtime, and expose `HEALTH_RECHECK_INTERVAL_SEC` as a class attribute.

## Scope

- **In-Scope**: Accepting timeout as parameter to `compute_health_check_timeout()`, exposing `HEALTH_RECHECK_INTERVAL_SEC` as class attribute
- **Out-of-Scope**: Changes to `HttpServerLifecycleManager.verify_running_async()` (handled in companion procedure), deleting dead code, consolidating shutdown logic

## Assumptions

- The timeout value passed to `compute_health_check_timeout()` will be the same as the current `MCPSERVER_HEALTH_TIMEOUT` constant from `agent.http_lifecycle`
- `HEALTH_RECHECK_INTERVAL_SEC` already exists at module level in `http_lifecycle_health_checker` and can be exposed as a class attribute

## Design decisions

- Accept timeout as a parameter rather than extracting it to a shared constants module — simpler and avoids creating a new dependency
- Expose `HEALTH_RECHECK_INTERVAL_SEC` as a class attribute so callers don't need to import from module level separately

## Alternatives considered

- Extracting timeout to a shared constants module — rejected because adding a parameter is simpler and avoids creating a new dependency
- Keeping the lazy import inside the method body — rejected because it's fragile under certain import orders

## Implementation

### Target file

scripts/agent/http_lifecycle_health_checker.py

### Procedure

Accept timeout as a parameter to `compute_health_check_timeout()` and expose `HEALTH_RECHECK_INTERVAL_SEC` as a class attribute.

### Method

#### Step 1: Verify current state

Verify `HealthChecker.compute_health_check_timeout()` currently imports `MCPSERVER_HEALTH_TIMEOUT` from `agent.http_lifecycle` at runtime. Confirm the circular import path.

#### Step 2: Add HEALTH_RECHECK_INTERVAL_SEC as class attribute

Add `HEALTH_RECHECK_INTERVAL_SEC = 10.0` as a class attribute on `HealthChecker`. This replaces the hardcoded `10.0` literal used elsewhere.

```python
class HealthChecker:
    """Health checker for MCP servers."""
    
    HEALTH_RECHECK_INTERVAL_SEC = 10.0
```

#### Step 3: Modify compute_health_check_timeout() signature

Change `compute_health_check_timeout()` to accept timeout as a parameter instead of importing it at runtime.

```python
def compute_health_check_timeout(self, timeout: float = None) -> float:
    """Compute the health check timeout.
    
    Args:
        timeout: Timeout value in seconds. Defaults to HEALTH_RECHECK_INTERVAL_SEC.
    
    Returns:
        Computed timeout value.
    """
    # Use provided timeout or fall back to class default
    timeout = timeout or self.HEALTH_RECHECK_INTERVAL_SEC
    
    # ... existing computation logic using timeout parameter
```

### Details

The full refactored `HealthChecker` class:

```python
class HealthChecker:
    """Health checker for MCP servers."""
    
    HEALTH_RECHECK_INTERVAL_SEC = 10.0
    
    def compute_health_check_timeout(self, timeout: float = None) -> float:
        """Compute the health check timeout.
        
        Args:
            timeout: Timeout value in seconds. Defaults to HEALTH_RECHECK_INTERVAL_SEC.
        
        Returns:
            Computed timeout value.
        """
        # Use provided timeout or fall back to class default
        timeout = timeout or self.HEALTH_RECHECK_INTERVAL_SEC
        
        # ... existing computation logic using timeout parameter
```

## Compatibility considerations

- Public API (`HealthChecker.compute_health_check_timeout()`) signature changes — timeout becomes an optional parameter
- Callers that previously relied on the implicit import will now get the default value
- Existing callers that pass timeout explicitly will continue to work

## Security considerations

- No security-relevant behavior changes — same validation and permission checks as before
- Parameter passing preserved exactly — no new attack surface from parameter addition

## Rollback considerations

- If parameter addition breaks behavior, revert to original method with lazy import
- Keep both signatures during transition period if needed

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| HealthChecker.compute_health_check_timeout() | Unit: verify no circular import under various import orders | `uv run python -c "from agent.http_lifecycle_health_checker import HealthChecker; print(HealthChecker.compute_health_check_timeout(5.0))"` | Returns correct timeout value |
| HEALTH_RECHECK_INTERVAL_SEC exposure | Unit: verify class attribute accessible | Manual inspection | Class attribute verified |
| Full test suite | Regression — all http_lifecycle tests | `uv run pytest tests/agent/ -q --ignore=tests/integration/` | All tests pass |
| Type checking | Static analysis | `uv run mypy scripts/agent/http_lifecycle*.py` | Clean |
| Linting | Style check | `uv run ruff check scripts/agent/http_lifecycle*.py` | Clean |

## Completion criteria

- `HealthChecker.compute_health_check_timeout()` accepts timeout as a parameter
- `HEALTH_RECHECK_INTERVAL_SEC` exposed as class attribute
- No circular import under any import order
- All existing tests pass
- No behavioral regression — same inputs produce same outputs
- Type checker passes on modified file
- Linter passes on modified file

## Out of scope

- Changes to `HttpServerLifecycleManager.verify_running_async()` (companion procedure)
- Deleting `ProcessSnapshotProvider` (separate procedure)
- Consolidating shutdown logic (companion procedure)
- Moving `_absorb_sigint_during_shutdown` between modules

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
- **Requirement ID**: REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-120000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-191140
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py
