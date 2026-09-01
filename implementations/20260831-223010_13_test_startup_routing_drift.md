## Goal

Update `tests/agent/test_startup_routing_drift.py` to import from new modules instead of `repl_health`.

## Scope

Modify `tests/agent/test_startup_routing_drift.py`: migrate imports to point to new modules (`routing_drift`). Key import locations: lines 39, 51, 62, 103.

## Assumptions

- `routing_drift.py` has been created first (Phase 2 complete)
- The `check_routing_drift`, `check_routing_safety_tiers` function signatures remain unchanged
- The test file currently imports from `repl_health` and needs to be migrated

## Design decisions

- Routing drift tests should import from `routing_drift` module
- Tests need `check_routing_drift` and `check_routing_safety_tiers` from `routing_drift`

## Alternatives considered

- Keeping all imports from `repl_health` via backward-compat re-exports — rejected because REQ-003 requires tests to pass after migration and importing from new modules is the correct long-term approach

## Implementation

### Target file

`tests/agent/test_startup_routing_drift.py`

### Procedure

1. Read current `test_startup_routing_drift.py:39,51,62,103` to identify existing import statements
2. Replace imports from `repl_health` with imports from `routing_drift`:
   ```python
   # Before:
   from agent.repl_health import check_routing_drift, check_routing_safety_tiers
   
   # After:
   from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers
   ```
3. Update any other import references throughout the file
4. Run tests after each change to verify they still pass

### Method

Direct import path update — replace the import source module name only.

### Details

```python
# Multiple import locations may need updating:
# Before:
#   from agent.repl_health import check_routing_drift, check_routing_safety_tiers
# After:
from agent.services.routing_drift import check_routing_drift, check_routing_safety_tiers
```

## Compatibility considerations

- REQ-003: All existing tests must pass after migration
- Tests should import from their respective new modules, not from the backward-compat layer

## Security considerations

N/A: This is a pure refactoring of import structure. No new security-sensitive code introduced.

## Rollback considerations

- Revert git changes to restore original imports if tests fail

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `test_startup_routing_drift.py` | Integration test: verify drift detection logic | `uv run pytest tests/agent/test_startup_routing_drift.py` | Drift tests pass |

## Completion criteria

- [ ] All imports updated to use `routing_drift` module (REQ-003)
- [ ] All existing tests pass after migration (REQ-003)
- [ ] No circular import errors when running tests

## Out of scope

- Changes to test logic or assertions
- Changes to `shared/` models/types used by tests
- Changes to `agent/lifecycle.py` or `agent/orchestrator.py` beyond existing patterns

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Wait for Phase 2 completion (all five new modules) | Pending | — | — | |
| 2 | Update imports in test_startup_routing_drift.py | Pending | — | — | |
| 3 | Run validation | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260831-152636_refactor_004_repl_health_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-223010_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-01T00:00:00Z
- **Related target files**: tests/agent/test_startup_routing_drift.py
