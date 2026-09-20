## Goal

Replace private attribute access from ShutdownCoordinator to HttpServerLifecycleManager with public method call per REQ-001.

## Scope

- Replace `manager._http_procs` direct access in ShutdownCoordinator with a public method call
- Use the newly added `iter_processes()` method instead of accessing `_http_procs` directly

## Assumptions

- The public API behavior of HttpServerLifecycleManager must be preserved exactly
- Existing test mocks reference component-level targets, not removed wrapper methods

## Design decisions

- Replace `manager._http_procs` with `manager.iter_processes()` in ShutdownCoordinator
- The iterator yields `(server_key, proc)` pairs, so the loop structure remains similar
- No changes to the shutdown logic itself — only the source of process iteration

## Alternatives considered

- Adding a property to expose `_http_procs` as read-only — rejected because it still exposes internal state layout
- Having ShutdownCoordinator maintain its own copy of processes — rejected because it creates synchronization issues

## Implementation
### Target file
scripts/agent/http_lifecycle_shutdown_coordinator.py

### Procedure
1. Replace `procs = manager._http_procs` with `for server_key, proc in manager.iter_processes():`
2. Remove the intermediate `procs` variable assignment
3. Update the loop to iterate over the yielded pairs directly

### Method
```python
# Before (line 88):
procs = manager._http_procs
terminator = terminator or manager.process_terminator
for server_key, proc in list(procs.items()):

# After:
terminator = terminator or manager.process_terminator
for server_key, proc in list(manager.iter_processes()):
```

### Details
- Line 88: Replace `procs = manager._http_procs` with direct iteration using `manager.iter_processes()`
- Line 90: Change `list(procs.items())` to `list(manager.iter_processes())`
- Remove the intermediate `procs` variable entirely

## Compatibility considerations

- `iter_processes()` is a new public method — no backward compatibility concerns
- The iterator returns items, not a snapshot — callers must consume it immediately
- No changes to existing public API behavior

## Security considerations

- No security implications — this is a refactoring of internal state access

## Rollback considerations

- Reverting requires restoring the `procs = manager._http_procs` line and updating the loop to use `procs.items()`

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Integration test for shutdown flow | uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py | All tests pass |
| scripts/agent/http_lifecycle.py | Unit test for iter_processes() method | uv run pytest tests/agent/test_http_lifecycle_integration.py | All tests pass |
| All modified files | Type checking | mypy scripts/agent/http_lifecycle*.py | No type errors |

## Completion criteria

- No private attribute access from ShutdownCoordinator to HttpServerLifecycleManager (`_http_procs`)
- All existing unit tests pass without modification
- Type checking passes on all modified files

## Out of scope

- Updating module docstrings (REQ-003) — handled separately
- Consolidating terminate poll interval constant (REQ-002) — handled separately
- Adding new features or changing public APIs beyond what refactoring achieves

## execution Status

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260920-125036_refactor_http_lifecycle_full_delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203054_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-222650
- **Related target files**: scripts/agent/http_lifecycle_shutdown_coordinator.py
