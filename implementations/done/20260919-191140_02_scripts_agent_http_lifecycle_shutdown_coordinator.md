## Goal

Consolidate shutdown logic into `ShutdownCoordinator.shutdown_all()` before delegating from `HttpServerLifecycleManager.shutdown_all()`, and fix `_http_procs` mutation ownership.

## Scope

- **In-Scope**: Adding `_http_procs` mutation (pop entries before termination) to `ShutdownCoordinator.shutdown_all()`, verifying `terminator` parameter usage
- **Out-of-Scope**: Changes to `HttpServerLifecycleManager.shutdown_all()` (handled in companion procedure), moving `_absorb_sigint_during_shutdown`, fixing circular imports, replacing hardcoded literals, splitting methods, deleting dead code

## Assumptions

- The `terminator` parameter in `ShutdownCoordinator.shutdown_all()` works correctly as-is — it defaults to `manager._process_terminator` when not supplied
- `HttpServerLifecycleManager.shutdown_all()` currently owns `_http_procs` mutation (pops entries before termination) — this behavior must be preserved after consolidation

## Design decisions

- Add `_http_procs` mutation to `ShutdownCoordinator.shutdown_all()` rather than removing it from `HttpServerLifecycleManager.shutdown_all()` — preserves ownership semantics and avoids breaking existing callers
- Verify `terminator` parameter works correctly before proceeding with delegation

## Alternatives considered

- Removing `_http_procs` mutation from `HttpServerLifecycleManager.shutdown_all()` instead of adding it to `ShutdownCoordinator.shutdown_all()` — rejected because it would change behavior and break existing callers
- Introducing a new method on `ShutdownCoordinator` specifically for `_http_procs` mutation — rejected because the existing `shutdown_all()` method should own all shutdown responsibilities

## Implementation

### Target file

scripts/agent/http_lifecycle_shutdown_coordinator.py

### Procedure

Add `_http_procs` mutation (pop entries before termination) to `ShutdownCoordinator.shutdown_all()` and verify `terminator` parameter usage.

### Method

#### Step 1: Verify current state

Verify `ShutdownCoordinator.shutdown_all()` exists and examine its current implementation. Confirm whether it already mutates `_http_procs` or if this needs to be added.

#### Step 2: Add _http_procs mutation

If `ShutdownCoordinator.shutdown_all()` does not already mutate `_http_procs`, add pop operations for each HTTP server process before calling the terminator. This ensures cleanup parity with `HttpServerLifecycleManager.shutdown_all()`.

The mutation should occur before termination, matching the pattern:
```python
# Before termination, remove from tracking
for proc_key in list(self._http_procs.keys()):
    self._http_procs.pop(proc_key, None)
```

#### Step 3: Verify terminator parameter usage

Confirm the `terminator` parameter is used correctly — it should default to `self._process_terminator` when not supplied. Verify this matches the usage pattern in `HttpServerLifecycleManager.shutdown_all()`.

### Details

```python
def shutdown_all(self, terminator=None):
    """Shut down all managed servers.
    
    Args:
        terminator: Optional ProcessTerminator instance. Defaults to self._process_terminator.
    """
    # Use provided terminator or fall back to instance default
    terminator = terminator or self._process_terminator
    
    # Mutate _http_procs before termination (matches HttpServerLifecycleManager behavior)
    for proc_key in list(self._http_procs.keys()):
        self._http_procs.pop(proc_key, None)
    
    # Terminate remaining processes
    for proc_key, proc_info in self._managed_servers.items():
        ...  # existing termination logic
```

## Compatibility considerations

- Public API (`ShutdownCoordinator.shutdown_all()`) signature unchanged — `terminator` parameter already optional
- Adding `_http_procs` mutation changes internal behavior but preserves external contract
- Existing callers of `ShutdownCoordinator.shutdown_all()` will see additional side effect (mutation) — this is intentional and required for correctness

## Security considerations

- No security-relevant behavior changes — same validation and permission checks as before
- Parameter passing preserved exactly — no new attack surface from mutation addition

## Rollback considerations

- If mutation breaks behavior, revert to original `ShutdownCoordinator.shutdown_all()` body without mutation
- Keep mutation conditional on a flag if needed during transition period

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| ShutdownCoordinator.shutdown_all() | Integration: verify _http_procs mutation parity | `uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py -v` | All shutdown tests pass |
| Terminator parameter | Unit: verify terminator defaults correctly | Manual inspection of code | Default behavior verified |
| Full test suite | Regression — all http_lifecycle tests | `uv run pytest tests/agent/ -q --ignore=tests/integration/` | All tests pass |
| Type checking | Static analysis | `uv run mypy scripts/agent/http_lifecycle*.py` | Clean |
| Linting | Style check | `uv run ruff check scripts/agent/http_lifecycle*.py` | Clean |

## Completion criteria

- `ShutdownCoordinator.shutdown_all()` mutates `_http_procs` (pops entries before termination)
- `terminator` parameter works correctly as-is (defaults to `self._process_terminator`)
- All existing shutdown tests pass
- No behavioral regression — same inputs produce same outputs
- Type checker passes on modified file
- Linter passes on modified file

## Out of scope

- Changes to `HttpServerLifecycleManager.shutdown_all()` (companion procedure)
- Moving `_absorb_sigint_during_shutdown` between modules
- Fixing circular imports in `HealthChecker.compute_health_check_timeout()`
- Replacing hardcoded literals with constant references
- Splitting `_cleanup_server_resources()` into two methods
- Deciding fate of `ProcessSnapshotProvider`
- Adding new unit tests (covered by companion procedure)

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260919-115306_refactor_002_consolidate_remaining_http_lifecycle_duplication_and_dead_code.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260919-120000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260919-191140
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
