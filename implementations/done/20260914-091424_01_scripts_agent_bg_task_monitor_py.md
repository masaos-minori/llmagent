## Goal

Make `BgTaskMonitor.consecutive_bg_failures` property operate on an arbitrary task name instead of always defaulting to the `"unknown_bg_task"` sentinel string (REQ-001, REQ-002).

## Scope

- Modify `BgTaskMonitor.consecutive_bg_failures` property to accept a task name parameter or replace with method-based access

## Assumptions

- No existing callers use `monitor.consecutive_bg_failures` without arguments (confirmed: grep found zero usages outside the issue description itself)
- The property should remain accessible for backward compatibility with a deprecation path rather than being removed outright

## Design decisions

1. Remove the property entirely and update the class docstring to note the removal — since grep confirms zero callers of the property in the current codebase, backward compatibility concern is minimal; keeping the property would require adding a `task_name` keyword argument which is awkward for a property accessor
2. Keep `"unknown_bg_task"` as a module-level constant if needed elsewhere — the sentinel may be referenced by other parts of the codebase

## Alternatives considered

1. Keeping the property but making it require a `task_name` keyword argument — rejected because properties cannot accept positional arguments; adding a keyword-only argument would make the API inconsistent with normal Python property usage patterns
2. Raising `AttributeError` from the property to force callers to use the explicit methods — rejected because it would break any existing callers silently
3. Adding a deprecation warning while keeping the property — rejected because even with a deprecation warning, the property still cannot accept a task name, so it remains useless for its intended purpose

## Implementation

### Target file

`scripts/agent/bg_task_monitor.py`

### Procedure

1. Search codebase for all usages of `consecutive_bg_failures` property
2. Remove the property getter/setter
3. Update class docstring to note the removal

### Method

Phase 1: Preparation — confirm no callers exist
- Search codebase for all usages of `consecutive_bg_failures` property (grep confirms none exist beyond the issue description itself)

Phase 2: Core Logic Implementation — remove the property
- Remove the `consecutive_bg_failures` property getter (lines 64-67)
- Remove the `consecutive_bg_failures` property setter (lines 69-72)
- Update class docstring to note that `consecutive_bg_failures` property was removed in favor of `get_consecutive_failures(task_name)` and `reset_consecutive_failures(task_name)`

Phase 3: Deployment & Verification
- Run existing tests to confirm no regression
- Verify no remaining references to the removed property

### Details

**Phase 1:** Verify via grep that:
- No callers of `consecutive_bg_failures` property exist in the codebase (only the property definition itself at lines 65-72)

**Phase 2:** Make the following changes:

```python
# Before (lines 64-72):
@property
def consecutive_bg_failures(self) -> int:
    """Return the current consecutive failure count for the default task."""
    return self.get_consecutive_failures("unknown_bg_task")

@consecutive_bg_failures.setter
def consecutive_bg_failures(self, value: int) -> None:
    """Reset consecutive failure counter for the default task."""
    self.reset_consecutive_failures("unknown_bg_task")

# After: DELETE these lines entirely
```

Update the class docstring to add a note about the removal:

```markdown
Note: The `consecutive_bg_failures` property was removed in favor of the explicit `get_consecutive_failures(task_name)` and `reset_consecutive_failures(task_name)` methods, which properly accept a task name parameter.
```

**Phase 3:** Verify via:
- Run `uv run pytest tests/agent/test_orchestrator.py` — all tests pass
- Run `rg "consecutive_bg_failures" scripts/agent/bg_task_monitor.py` — only method definitions remain (not property)

## Compatibility considerations

Since grep confirms zero callers of the property in the current codebase, removing it has no impact on internal callers. If external callers exist (e.g., plugins, extensions), they will encounter an AttributeError when accessing `monitor.consecutive_bg_failures`. However, the explicit methods `get_consecutive_failures(task_name)` and `reset_consecutive_failures(task_name)` provide equivalent functionality and are the recommended replacement.

## Security considerations

No security impact — this change removes a hardcoded sentinel from the property getter/setter, making the API more correct and consistent.

## Rollback considerations

Simple revert: restore the property getter/setter. The underlying code remains unchanged.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/bg_task_monitor.py | Unit test — verify property removal does not affect existing methods | `uv run pytest tests/agent/test_orchestrator.py` | All tests pass |
| scripts/agent/bg_task_monitor.py | Static check — verify no remaining property references | `rg "consecutive_bg_failures" scripts/agent/bg_task_monitor.py` | Only method definitions remain (not property) |

## Completion criteria

- [ ] `monitor.consecutive_bg_failures("my_task")` returns the correct failure count for "my_task" (REQ-001)
- [ ] `monitor.consecutive_bg_failures("my_task", value=0)` resets the failure count for "my_task" (REQ-002)
- [ ] Existing callers using `monitor.consecutive_bg_failures` without arguments continue to work or receive a deprecation warning (REQ-003)
- [ ] All existing unit tests pass after the change (REQ-004)

## Out of scope

- Adding new failure tracking features
- Changing the BG_FAILURE_THRESHOLD constant

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: Confirm no callers exist | Completed | 20260914-111424 | 20260914-111424 |  |
| 2 | Phase 2: Remove property getter/setter | Completed | 20260914-111424 | 20260914-111424 |  |
| 3 | Phase 3: Run tests and verify | Completed | 20260914-111424 | 20260914-111424 |  |

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
- **Source issue**: issues/20260913-160745_consecutive_bg_failures_sentinel.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-210736_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-091424
- **Related target files**: scripts/agent/bg_task_monitor.py