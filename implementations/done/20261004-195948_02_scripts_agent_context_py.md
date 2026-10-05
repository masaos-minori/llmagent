## Goal

Verify that `AgentContext.services_required` property and AppServices invariant are compatible with the proposed assertion-based enforcement.

## Scope

- Read `scripts/agent/context.py`: understand services_required property and AppServices invariant

## Assumptions

- The services_required property returns an AppServices instance
- The AppServices constructor already enforces the invariant (per as010 plan)
- The property should also enforce the invariant at access time as a defense-in-depth measure

## Design decisions

- No modification needed — this is a read-only verification step
- If the property does not exist or is inaccessible, report as Blocked

## Alternatives considered

- Modifying the services_required property to add assertions — over-engineering if AppServices constructor already enforces the invariant
- Adding a separate validation method — unnecessary duplication

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

Read and verify the services_required property definition and AppServices invariant.

### Method

1. Locate the services_required property in `scripts/agent/context.py`
2. Verify the property returns an AppServices instance
3. Confirm the invariant is enforced at both construction time (AppServices.__init__) and access time (property getter)

### Details

```python
# Expected structure in scripts/agent/context.py:
class AgentContext:
    """..."""
    
    def __init__(self, ...):
        self._services_required: Optional[AppServices] = None
    
    @property
    def services_required(self) -> AppServices:
        """Return the required services object."""
        if self._services_required is None:
            raise AssertionError("services_required must be set before use")
        return self._services_required
```

If the property exists and is accessible, proceed to the next step. Otherwise, report as Blocked.

### Source-verified outcome

Adversarial verification (workflow Step 3a) confirms the property exists and the
invariant holds, but the mechanism differs from the "Expected structure" above:

- `AgentContext.services_required` (context.py:336) returns the `AppServices`
  instance and raises `RuntimeError` (not `AssertionError`) when unset —
  defense-in-depth at access time.
- Per-service non-None invariant is enforced at construction in
  `AppServices.__init__` (context.py:270-280, commit `10308ed7`), raising
  `RuntimeError` on any missing required service.
- The property is accessible from ReadinessReporter: `scripts/agent/startup_reporter.py`
  reads `self._ctx.services_required.runtime_tools` / `.health_registry`.

Conclusion: read-only verification passed. Completion criterion met. No
modification made (this is a read-only step).

## Compatibility considerations

N/A: This is a read-only verification step.

## Security considerations

N/A: No security impact.

## Rollback considerations

N/A: No changes made.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/context.py | Verification — confirm property exists and is accessible | Manual inspection | Property exists and is accessible |

## Completion criteria

- [ ] `AgentContext.services_required` property exists and is accessible from ReadinessReporter

## Out of scope

- Modifying the services_required property or its methods
- Creating new test file (handled in separate document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261005-225213 | 20261005-225213 | Read-only verification performed; services_required property (context.py:336) and AppServices construction-time invariant (context.py:270-280, 10308ed7) confirmed. See Source-verified outcome. |
| 2 | Add or update tests per Validation plan | Completed | 20261005-225213 | 20261005-225213 | N/A: read-only step; no test authored (test_startup_reporter.py created by sibling ..._03_...). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261005-225213 | 20261005-225213 | Property accessible from ReadinessReporter; existing test_context.py passes (verified in #1 cycle). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261005-225213 | 20261005-225213 | N/A: read-only step, no code change -> no docs/00_index.md task-scope mapping. |

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
- **Source issue**: issues/20261004-143010_rr011_services_invariant_uncertainty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182818_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195948
- **Related target files**: scripts/agent/context.py