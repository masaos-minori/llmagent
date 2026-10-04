## Goal

Resolve the inconsistency between the docstring claim ("All required services are non-None") and the defensive null checks in ReadinessReporter by enforcing the invariant via assertion.

## Scope

- Modify `scripts/agent/startup_reporter.py`: add assertion in `AgentContext.services_required` property OR remove redundant defensive null checks
- Modify `scripts/agent/context.py`: read-only verification of services_required property

## Assumptions

- Option A (enforce invariant) aligns with Issue 10's approach of validating at construction time
- The invariant can realistically be guaranteed since factory.py always provides non-None values for required services
- Removing defensive null checks is safe because the invariant will be enforced at construction time

## Design decisions

- Enforce the invariant via assertion in `AgentContext.services_required` property (Option A preferred)
- Remove redundant defensive null checks in `report_readiness()` after invariant enforcement
- Use AssertionError which is caught by test suites but not production error handlers

## Alternatives considered

- Documenting why defensive checks exist despite the docstring claim (Option B) — simpler but leaves the invariant unenforced
- Adding runtime validation only in report_readiness() — doesn't address root cause

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

Add assertion in AgentContext.services_required property to validate invariant. Remove redundant defensive null checks in report_readiness().

### Method

1. Locate lines 97-111 in `scripts/agent/startup_reporter.py` (defensive null checks on services_required)
2. Add assertion in AgentContext.services_required property to validate all required sub-services are present
3. Remove redundant defensive null checks in report_readiness()

### Details

```python
# Before (lines 97-111 in startup_reporter.py):
def report_readiness(self) -> dict:
    if self._ctx.services_required is None:
        return {"status": "unavailable", "reason": "No services configured"}
    
    result = {
        "http": self._ctx.services_required.http is not None,
        "llm": self._ctx.services_required.llm is not None,
        ...
    }
    return result

# After:
def report_readiness(self) -> dict:
    # No longer need defensive null check — invariant enforced at construction
    result = {
        "http": self._ctx.services_required.http is not None,
        "llm": self._ctx.services_required.llm is not None,
        ...
    }
    return result
```

Additionally, in `scripts/agent/context.py`, add assertion in the services_required property:

```python
# In AgentContext class:
@property
def services_required(self) -> AppServices:
    """Return the required services object.
    
    Raises:
        AssertionError: If any required service is None (invariant violation).
    """
    if self._services_required is None:
        raise AssertionError("services_required must be set before use")
    
    # Enforce invariant: all required services must be non-None
    for _name, _svc in [("http", self._services_required.http),
                        ("llm", self._services_required.llm),
                        ("tools", self._services_required.tools),
                        ("lifecycle", self._services_required.lifecycle),
                        ("hist_mgr", self._services_required.hist_mgr),
                        ("audit_logger", self._services_required.audit_logger)]:
        if _svc is None:
            raise AssertionError(f"Required service '{_name}' is None — invariant violated")
    
    return self._services_required
```

The key changes are:
1. Assertion in services_required property validates the invariant at access time
2. Removal of redundant defensive null checks in report_readiness()

## Compatibility considerations

This change is backward-compatible — it adds a protection mechanism that was previously absent. No existing behavior is lost for cases where the invariant holds. However, callers relying on the defensive null checks may see different error types (AssertionError vs None handling).

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original defensive null checks if callers depend on graceful handling of missing services. This would restore the previous behavior but leave the invariant unenforced.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_reporter.py | Unit test — verify readiness reporting consistency | uv run pytest tests/agent/test_startup_reporter.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Either invariant enforced at construction OR defensive checks documented (REQ-001)
- [ ] No ambiguity between docstring claims and implementation behavior (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to services_required property implementation
- Changes to the readiness report format
- Creating new test file (handled in separate document)

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
- **Source plan**: plans/20261004-182818_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195948
- **Related target files**: scripts/agent/startup_reporter.py
