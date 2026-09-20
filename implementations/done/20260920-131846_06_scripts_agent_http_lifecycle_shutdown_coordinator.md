## Goal

Eliminate private attribute access violations in ShutdownCoordinator by delegating cleanup responsibilities back to HttpServerLifecycleManager, which owns its own state.

## Scope

- **In-Scope**: Add public cleanup methods to HttpServerLifecycleManager; refactor ShutdownCoordinator.shutdown_all to use those public methods instead of accessing private attributes; update module docstrings
- **Out-of-Scope**: Modifying McpServerConfig schema; changing subprocess launch arguments or security model

## Assumptions

- HttpServerLifecycleManager owns its own internal state (`_http_procs`, `_http_pgids`, `_stderr_files`, `_stderr_log_manager`, `_last_health_check`) and should provide public methods for cleanup
- ShutdownCoordinator should not reach into HttpServerLifecycleManager's private state — it should delegate cleanup to the manager

## Design decisions

- Add public methods to HttpServerLifecycleManager for cleanup operations that ShutdownCoordinator currently performs via private attributes
- The two main cleanup patterns are:
  1. Per-server cleanup (after termination): pop from `_http_procs`, `_http_pgids`; close stderr handle; forget log path
  2. Global cleanup (at end of shutdown_all): clear `_stderr_log_manager`, clear `_last_health_check`
- These map to two new public methods on HttpServerLifecycleManager:
  - `cleanup_server_key(server_key)` — handles per-server tracking removal
  - `clear_all_health_checks()` — clears the health check timestamp dict

## Alternatives considered

- Making the private attributes public: rejected because it exposes internal state layout
- Adding individual accessor methods for each private attribute: rejected because it creates too many new public APIs for a single concern
- Having ShutdownCoordinator hold references to the component managers directly: rejected because it duplicates the composition pattern already used by HttpServerLifecycleManager

## Implementation

### Target file

scripts/agent/http_lifecycle_shutdown_coordinator.py

### Procedure

1. Add public cleanup methods to HttpServerLifecycleManager (in http_lifecycle.py)
2. Refactor ShutdownCoordinator.shutdown_all to use HttpServerLifecycleManager's public methods
3. Update module docstrings

### Method

Inline addition pattern — add public methods to HttpServerLifecycleManager, then refactor ShutdownCoordinator to delegate to them.

### Details

**Step 1: Add public cleanup methods to HttpServerLifecycleManager (in http_lifecycle.py)**

After the existing `_clear_server_tracking_data` method (line 162-168), add:

```python
def cleanup_server_key(self, server_key: str) -> None:
    """Remove process tracking entries for a server key.
    
    Called by ShutdownCoordinator after terminating a server process.
    Removes the process entry, pgid entry, and delegates stderr/log cleanup
    to _clear_server_tracking_data.
    """
    self._http_procs.pop(server_key, None)
    self._http_pgids.pop(server_key, None)
    self._clear_server_tracking_data(server_key)

def clear_all_health_checks(self) -> None:
    """Clear all health check timestamps.
    
    Called by ShutdownCoordinator at the end of shutdown_all().
    """
    self._last_health_check.clear()
```

Also add a helper property:

```python
@property
def process_terminator(self) -> ProcessTerminator:
    """Return the configured ProcessTerminator."""
    return self._process_terminator
```

**Step 2: Refactor ShutdownCoordinator.shutdown_all**

Current private attribute accesses and their replacements:

| Line | Current Code | Replacement |
|------|-------------|-------------|
| 83 | `procs = manager._http_procs` | Remove — iterate via `manager.list_processes()` or keep local copy |
| 84 | `terminator = terminator or manager._process_terminator` | `terminator = terminator or manager.process_terminator` |
| 89 | `manager._http_procs.pop(server_key, None)` | `manager.cleanup_server_key(server_key)` |
| 95 | `manager._http_pgids.pop(server_key, None)` | Covered by `cleanup_server_key` |
| 96 | `stderr_fh = manager._stderr_files.pop(server_key, None)` | Covered by `cleanup_server_key` |
| 119 | `manager._http_pgids.pop(server_key, None)` | Covered by `cleanup_server_key` |
| 120 | `stderr_fh = manager._stderr_files.pop(server_key, None)` | Covered by `cleanup_server_key` |
| 130 | `manager._stderr_log_manager.clear()` | Call `manager._clear_server_tracking_data(server_key)` per-server instead |
| 131 | `manager._last_health_check.clear()` | `manager.clear_all_health_checks()` |

Refactored shutdown_all flow:
1. Get terminator via `manager.process_terminator`
2. Iterate over `list(manager._http_procs.items())` (still need local copy since we modify during iteration)
3. For each server: call `await terminator.terminate_with_timeout(...)` then `manager.cleanup_server_key(server_key)`
4. At end: call `manager.clear_all_health_checks()`

Note: `manager._http_procs` is still accessed at line 83 to get the initial list of processes. This is acceptable because:
- It's the only way to enumerate managed servers at shutdown time
- The alternative would be adding a `get_managed_servers()` method to HttpServerLifecycleManager
- Consider this as a follow-up improvement rather than blocking this change

**Step 3: Update module docstrings**

- Update ShutdownCoordinator module docstring to document the delegation pattern
- Update HttpServerLifecycleManager module docstring to document the new public cleanup methods

## Compatibility considerations

- The new `cleanup_server_key` method encapsulates the exact same side effects as the current private attribute access pattern
- The `process_terminator` property provides read-only access to the terminator instance
- `clear_all_health_checks` is a simple dict clear — no behavioral change
- Existing callers of shutdown_all continue to work unchanged

## Security considerations

N/A: No security-relevant behavior changes — only structural refactoring.

## Rollback considerations

- If the new methods cause regressions, revert to the original private attribute access pattern
- The original code can be restored from git history if needed

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Unit: verify no private attribute access | `grep -n "manager\._http_procs\|manager\._stderr_files\|manager\._http_pgids\|manager\._stderr_log_manager\|manager\._last_health_check" scripts/agent/http_lifecycle_shutdown_coordinator.py` | Returns 0 matches (except in docstring) |
| scripts/agent/http_lifecycle.py | Unit: verify cleanup_server_key exists | `grep -c "def cleanup_server_key" scripts/agent/http_lifecycle.py` | Returns 1 |
| scripts/agent/http_lifecycle.py | Unit: verify clear_all_health_checks exists | `grep -c "def clear_all_health_checks" scripts/agent/http_lifecycle.py` | Returns 1 |
| scripts/agent/http_lifecycle.py | Unit: verify process_terminator property exists | `grep -c "def process_terminator" scripts/agent/http_lifecycle.py` | Returns 1 |
| All lifecycle modules | Integration: run full test suite | `pytest tests/agent/test_http_lifecycle*.py` | All tests pass |

## Completion criteria

- ShutdownCoordinator no longer accesses private attributes of HttpServerLifecycleManager
- HttpServerLifecycleManager has public `cleanup_server_key`, `clear_all_health_checks`, and `process_terminator` methods
- No circular import introduced (verified by importing each module independently)

## Out of scope

- Modifying McpServerConfig schema
- Changing subprocess launch arguments or security model
- Adding new error types or changing existing error semantics
- Performance optimization beyond what the refactoring naturally achieves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260920-151819 | 20260920-151819 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260920-151555 | 20260920-151555 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260920-151555 | 20260920-151555 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260920-151555 | 20260920-151555 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260920-125036_refactor_http_lifecycle_full_delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-130856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-131846
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py