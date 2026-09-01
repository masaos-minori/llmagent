## Goal

Update `tests/agent/test_audit_security_failures.py` to import from new modules instead of `repl_health`.

## Scope

Modify `tests/agent/test_audit_security_failures.py`: migrate imports to point to new modules (`security_audit`). Key import locations: lines 39, 53, 70, 86, 105, 122, 142, 163, 187, 202.

## Assumptions

- `security_audit.py` has been created first (Phase 2 complete)
- The `audit_security_defaults` function signature remains unchanged
- The test file currently imports from `repl_health` and needs to be migrated

## Design decisions

- Security audit tests should import from `security_audit` module
- Tests need `audit_security_defaults` and potentially `_load_audit_config_or_warn` from `security_audit`

## Alternatives considered

- Keeping all imports from `repl_health` via backward-compat re-exports — rejected because REQ-003 requires tests to pass after migration and importing from new modules is the correct long-term approach

## Implementation

### Target file

`tests/agent/test_audit_security_failures.py`

### Procedure

1. Read current `test_audit_security_failures.py:39,53,70,86,105,122,142,163,187,202` to identify existing import statements
2. Replace imports from `repl_health` with imports from `security_audit`:
   ```python
   # Before:
   from agent.repl_health import audit_security_defaults, _load_audit_config_or_warn
   
   # After:
   from agent.services.security_audit import audit_security_defaults, _load_audit_config_or_warn
   ```
3. Update any other import references throughout the file
4. Run tests after each change to verify they still pass

### Method

Direct import path update — replace the import source module name only.

### Details

```python
# Multiple import locations may need updating:
# Before:
#   from agent.repl_health import audit_security_defaults, _load_audit_config_or_warn
# After:
from agent.services.security_audit import audit_security_defaults, _load_audit_config_or_warn
```

## Compatibility considerations

- REQ-003: All existing tests must pass after migration
- Tests should import from their respective new modules, not from the backward-compat layer

## Security considerations

- This test file validates security defaults auditing behavior
- Ensure `_load_audit_config_or_warn` handles missing/warn scenarios correctly during testing

## Rollback considerations

- Revert git changes to restore original imports if tests fail

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `test_audit_security_failures.py` | Unit test: verify audit findings classification | `uv run pytest tests/agent/test_audit_security_failures.py` | Audit failure tests pass |

## Completion criteria

- [ ] All imports updated to use `security_audit` module (REQ-003)
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
| 1 | Wait for Phase 2 completion (all five new modules) | Completed | — | — | |
| 2 | Update imports in test_audit_security_failures.py | Completed | — | — | Already migrated; no changes needed |
| 3 | Run validation | Completed | — | — | All 10 tests pass |

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
- **Related target files**: tests/agent/test_audit_security_failures.py
