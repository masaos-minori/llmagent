## Goal

Remove redundant defensive null checks in ReadinessReporter.report_readiness() after invariant enforcement via AppServices constructor validation.

## Scope

- Modify `scripts/agent/startup_reporter.py`: remove null checks on `self._ctx.services_required` in `report_readiness()`

## Assumptions

- Plan 11 (as010) adds constructor validation for required services — verified via source inspection
- The invariant "all required services are non-None" now holds at construction time
- Removing null checks is safe because the invariant will be enforced at construction time

## Design decisions

- Remove redundant defensive null checks in `report_readiness()` after invariant enforcement
- Keep the rest of the method unchanged — only null checks removed

## Alternatives considered

- Documenting why defensive checks exist despite the docstring claim (Option B) — simpler but leaves the invariant unenforced
- Adding assertion in AgentContext.services_required property — doesn't address root cause

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

Remove redundant defensive null checks on `self._ctx.services_required` in `report_readiness()`.

### Method

1. Locate lines 97-101 in `scripts/agent/startup_reporter.py` (null check for `services_required` before accessing `runtime_tools`)
2. Replace ternary expression with direct access
3. Locate lines 107-111 in `scripts/agent/startup_reporter.py` (null check for `services_required` before accessing `health_registry`)
4. Replace ternary expression with direct access

### Details

```python
# Before (lines 97-101):
runtime_tools = (
    self._ctx.services_required.runtime_tools
    if self._ctx.services_required
    else None
)

# After:
runtime_tools = self._ctx.services_required.runtime_tools

# Before (lines 107-111):
registry = (
    self._ctx.services_required.health_registry
    if self._ctx.services_required
    else None
)

# After:
registry = self._ctx.services_required.health_registry
```

The key change is removing the conditional ternary expressions and replacing them with direct attribute access. The invariant ensures `self._ctx.services_required` is never None when accessed.

## Compatibility considerations

This change is backward-compatible — it removes protection that was previously absent. No existing behavior is lost for cases where the invariant holds. Callers relying on the defensive null checks may see AttributeError instead of None handling if the invariant is violated.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original defensive null checks if callers depend on graceful handling of missing services. This would restore the previous behavior but leave the invariant unenforced.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_reporter.py | Integration: verify readiness reporting works correctly | uv run pytest | Tests pass without errors |

## Completion criteria

- [ ] Defensive null checks removed from report_readiness() (REQ-001)
- [ ] All tests pass when run individually

## Out of scope

- Changes to services_required property implementation
- Changes to the readiness report format
- Creating new test file (handled separately)

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
- **Source issue**: issues/20261004-143010_rr011_services_invariant_uncertainty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-115000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-090000
- **Related target files**: scripts/agent/startup_reporter.py
