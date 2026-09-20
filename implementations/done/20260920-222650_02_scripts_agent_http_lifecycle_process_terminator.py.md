## Goal

Remove duplicate `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` constant and import from http_lifecycle.py per REQ-002.

## Scope

- Remove `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` from ProcessTerminator
- Import `_TERMINATE_POLL_INTERVAL_SEC` from http_lifecycle.py instead
- Update any references to use the imported constant

## Assumptions

- The two constants serve slightly different purposes (different default values: 0.05 vs 0.1) but should share a single source of truth
- Existing test mocks reference component-level targets, not removed wrapper methods

## Design decisions

- Import `_TERMINATE_POLL_INTERVAL_SEC` from http_lifecycle.py into ProcessTerminator
- Use the imported constant as the default value for `terminate_poll_interval_sec` parameter
- Keep the value 0.05 (the current value used by `_wait_exited` in http_lifecycle.py)

## Alternatives considered

- Keeping both constants separate with docstring comments explaining the difference — rejected because it creates configuration drift risk when developers assume they align
- Making the constant configurable via constructor parameter only — rejected because it would require updating all callers

## Implementation
### Target file
scripts/agent/http_lifecycle_process_terminator.py

### Procedure
1. Remove `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` constant definition
2. Import `_TERMINATE_POLL_INTERVAL_SEC` from http_lifecycle.py
3. Update the default value in `__init__` to use the imported constant

### Method
```python
# Remove line 19: _DEFAULT_TERMINATE_POLL_INTERVAL_SEC: float = 0.1

# Add import after existing imports:
from agent.http_lifecycle import _TERMINATE_POLL_INTERVAL_SEC

# Update __init__ method (around line 30):
self._terminate_poll_interval_sec = (
    terminate_poll_interval_sec
    if terminate_poll_interval_sec is not None
    else _TERMINATE_POLL_INTERVAL_SEC
)
```

### Details
- Line 19: Remove `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC: float = 0.1`
- After line 17 (`logger = logging.getLogger(__name__)`), add import statement
- Line 30-34: Update the default value assignment to use `_TERMINATE_POLL_INTERVAL_SEC` instead of `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC`

## Compatibility considerations

- Removing `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` breaks ProcessTerminator's default behavior — mitigated by verifying the constant is used only as a default and can safely be replaced with an import
- No changes to public API behavior

## Security considerations

- No security implications — this is a refactoring of internal constants

## Rollback considerations

- Reverting requires restoring `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` in ProcessTerminator and removing the import

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_process_terminator.py | Unit test for constant import | uv run pytest tests/agent/test_http_lifecycle_integration.py | All tests pass |
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Integration test for shutdown flow | uv run pytest tests/agent/test_http_lifecycle_shutdown_coordinator.py | All tests pass |
| All modified files | Type checking | mypy scripts/agent/http_lifecycle*.py | No type errors |

## Completion criteria

- `_DEFAULT_TERMINATE_POLL_INTERVAL_SEC` is removed from ProcessTerminator
- `_TERMINATE_POLL_INTERVAL_SEC` is imported from http_lifecycle.py
- All existing unit tests pass without modification
- Type checking passes on all modified files

## Out of scope

- Updating module docstrings (REQ-003) — handled separately
- Modifying ShutdownCoordinator to use the new method (handled separately)
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260920-125036_refactor_http_lifecycle_full_delegation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-203054_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-222650
- **Related target files**: scripts/agent/http_lifecycle_process_terminator.py
