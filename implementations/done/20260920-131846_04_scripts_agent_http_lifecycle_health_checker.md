## Goal

Resolve circular import between HealthChecker and http_lifecycle.py by replacing the dynamic import of `MCPSERVER_HEALTH_TIMEOUT` with a parameter-based approach.

## Scope

- **In-Scope**: Remove `from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT` from HealthChecker; update `HealthChecker.compute_health_check_timeout` to accept `mcpserver_health_timeout` as a parameter; update all callers to pass `MCPSERVER_HEALTH_TIMEOUT`; update docstrings referencing `MCPSERVER_HEALTH_TIMEOUT`
- **Out-of-Scope**: Modifying health check HTTP endpoint URLs or status code expectations

## Assumptions

- No callers outside the agent package depend on `MCPSERVER_HEALTH_TIMEOUT` (verified via grep)
- `HealthChecker.compute_health_check_timeout` currently accepts `startup_timeout` as a parameter — it can receive `MCPSERVER_HEALTH_TIMEOUT` as an additional parameter instead of importing it

## Design decisions

- **Preferred approach**: Pass `MCPSERVER_HEALTH_TIMEOUT` as a parameter to `HealthChecker.compute_health_check_timeout` rather than moving the constant into HealthChecker. This avoids duplicating the constant value and keeps the single source of truth in one place.
- **Alternative**: Create a dedicated config/constants module for cross-module constants if other health-check constants need sharing across modules.

## Alternatives considered

- Moving `MCPSERVER_HEALTH_TIMEOUT` into HealthChecker: rejected because it would duplicate the constant value and create two sources of truth
- Creating a dedicated config module: acceptable alternative if other health-check constants also need sharing

## Implementation

### Target file

scripts/agent/http_lifecycle_health_checker.py

### Procedure

1. Remove the circular import from HealthChecker
2. Update `compute_health_check_timeout` signature to accept `mcpserver_health_timeout` parameter
3. Update all callers to pass `MCPSERVER_HEALTH_TIMEOUT` as the timeout argument
4. Update docstrings referencing `MCPSERVER_HEALTH_TIMEOUT`

### Method

Inline replacement pattern — replace the dynamic import with a parameter-based approach.

### Details

**Step 1: Remove circular import**

- Delete line 33: `from agent.http_lifecycle import MCPSERVER_HEALTH_TIMEOUT`
- Update docstring at lines 29-31: remove reference to `MCPSERVER_HEALTH_TIMEOUT`, describe the parameter-based approach instead

**Step 2: Update compute_health_check_timeout signature**

- Current signature: `compute_health_check_timeout(startup_timeout: float) -> float`
- New signature: `compute_health_check_timeout(startup_timeout: float, mcpserver_health_timeout: float = 5.0) -> float`
- Replace `return min(MCPSERVER_HEALTH_TIMEOUT, startup_timeout)` with `return min(mcpserver_health_timeout, startup_timeout)`

**Step 3: Update callers**

- Find all callers of `HealthChecker.compute_health_check_timeout` within http_lifecycle.py
- Line 368: `self._health_checker.compute_health_check_timeout(cfg.startup_timeout_sec)` → `self._health_checker.compute_health_check_timeout(cfg.startup_timeout_sec, MCPSERVER_HEALTH_TIMEOUT)`
- `MCPSERVER_HEALTH_TIMEOUT` is already imported in http_lifecycle.py (line 45), so no additional import needed

**Step 4: Update docstrings**

- Update docstring at lines 29-31 to reflect that timeout is now passed as a parameter

## Compatibility considerations

- All callers of `compute_health_check_timeout` must be updated simultaneously
- The default value of 5.0 for `mcpserver_health_timeout` ensures backward compatibility if called without the new parameter

## Security considerations

N/A: No security-relevant behavior changes — only structural refactoring.

## Rollback considerations

- If caller updates cause regressions, revert to the original dynamic import approach
- The original import can be restored from git history if needed

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_health_checker.py | Unit: verify no http_lifecycle import | `grep -c "from agent.http_lifecycle import" scripts/agent/http_lifecycle_health_checker.py` | Returns 0 |
| scripts/agent/http_lifecycle_health_checker.py | Unit: verify compute_health_check_timeout accepts timeout param | `grep "mcpserver_health_timeout" scripts/agent/http_lifecycle_health_checker.py` | Returns 1+ match |
| scripts/agent/http_lifecycle.py | Integration: verify caller passes MCPSERVER_HEALTH_TIMEOUT | `grep "compute_health_check_timeout" scripts/agent/http_lifecycle.py` | Shows MCPSERVER_HEALTH_TIMEOUT argument |
| All lifecycle modules | Integration: run full test suite | `pytest tests/agent/test_http_lifecycle*.py` | All tests pass |

## Completion criteria

- HealthChecker no longer imports from http_lifecycle.py
- `compute_health_check_timeout` accepts `mcpserver_health_timeout` as a parameter
- All callers updated to pass `MCPSERVER_HEALTH_TIMEOUT`
- Circular import eliminated (verified by importing each module independently)

## Out of scope

- Modifying McpServerConfig schema
- Changing subprocess launch arguments or security model
- Adding new error types or changing existing error semantics
- Performance optimization beyond what the refactoring naturally achieves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-151756 | 20260920-151756 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-151535 | 20260920-151535 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-151535 | 20260920-151535 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-151535 | 20260920-151535 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260920-125036_refactor_http_lifecycle_full_delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-130856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131846
- **Related target files**: scripts/agent/http_lifecycle_health_checker.py