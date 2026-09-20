## Goal

Add public method for process iteration and consolidate terminate poll interval constant per REQ-001 and REQ-002.

## Scope

- Add `iter_processes()` public method to yield `(server_key, proc)` pairs from `_http_procs`
- Consolidate `_TERMINATE_POLL_INTERVAL_SEC` as single source of truth for terminate poll interval

## Assumptions

- The two constants serve slightly different purposes (different default values: 0.05 vs 0.1) but should share a single source of truth
- Existing test mocks reference component-level targets, not removed wrapper methods

## Design decisions

- `iter_processes()` returns an iterator over items, not the dict itself — callers cannot modify the underlying dict
- Move `_TERMINATE_POLL_INTERVAL_SEC` to http_lifecycle.py, remove `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` from ProcessTerminator, import from http_lifecycle.py
- Keep the value 0.05 in http_lifecycle.py (the current value used by `_wait_exited`)

## Alternatives considered

- Keeping both constants separate with docstring comments explaining the difference — rejected because it creates configuration drift risk when developers assume they align
- Adding a parameter to `shutdown_all()` instead of exposing iteration — rejected because it couples ShutdownCoordinator to HttpServerLifecycleManager's internal state layout

## Implementation
### Target file
scripts/agent/http_lifecycle.py

### Procedure
1. Add `iter_processes()` public method that yields `(server_key, proc)` pairs from `_http_procs`
2. Move `_TERMINATE_POLL_INTERVAL_SEC` definition to be the canonical location (already here at line 51)
3. Update any references to use the consolidated constant

### Method
```python
def iter_processes(self) -> Iterator[tuple[str, subprocess.Popen[bytes]]]:
    """Yield (server_key, proc) pairs for all managed HTTP subprocess servers.
    
    This method provides controlled access to managed processes without
    exposing the internal `_http_procs` dictionary directly. Callers receive
    an iterator and cannot modify the underlying dictionary.
    """
    for key, proc in self._http_procs.items():
        yield key, proc
```

### Details
- Line 51: `_TERMINATE_POLL_INTERVAL_SEC: float = 0.05` — keep as-is, this is the canonical location
- After line 231 (`list_processes` method), add new `iter_processes()` method
- Import `Iterator` from `typing` module if not already imported
- Update `_wait_exited` method to use the constant (already uses it at line 121)

## Compatibility considerations

- `iter_processes()` is a new public method — no backward compatibility concerns
- The method returns an iterator, not a snapshot, so callers must consume it immediately
- No changes to existing public API behavior

## Security considerations

- The iterator exposes process objects but not the internal dictionary — callers cannot add/remove entries
- No sensitive data exposure beyond what `verify_running()` and other methods already expose

## Rollback considerations

- Removing `iter_processes()` is safe if needed — it's a new addition with no dependencies
- Reverting constant consolidation requires restoring `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` in ProcessTerminator

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle.py | Unit test for new iter_processes() method | uv run pytest tests/agent/test_http_lifecycle_integration.py | All tests pass |
| scripts/agent/http_lifecycle_process_terminator.py | Unit test for constant import | uv run pytest tests/agent/test_http_lifecycle_integration.py | All tests pass |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Integration test for shutdown flow | uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py | All tests pass |
| All modified files | Type checking | mypy scripts/agent/http_lifecycle*.py | No type errors |

## Completion criteria

- `iter_processes()` method exists and yields correct `(server_key, proc)` pairs
- `_TERMINATE_POLL_INTERVAL_SEC` is the single source of truth for terminate poll interval
- All existing unit tests pass without modification
- Type checking passes on all modified files

## Out of scope

- Updating module docstrings (REQ-003) — handled separately
- Modifying ShutdownCoordinator to use the new method (handled separately)
- Adding new features or changing public APIs beyond what refactoring achieves

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260920-125036_refactor_http_lifecycle_full_delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203054_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-222650
- **Related target files**: scripts/agent/http_lifecycle.py
