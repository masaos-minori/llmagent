## Goal

Enforce the invariant that all required services are non-None at construction time, preventing silent creation of invalid objects.

## Scope

- Modify `scripts/agent/context.py`: add None-check validation in `AppServices.__init__()`
- Update docstring to clarify optional vs required services

## Assumptions

- `memory` is intentionally allowed to be None (per existing docstring)
- Adding runtime validation won't break existing callers since they should already pass non-None values
- The RuntimeError message format should match existing patterns in the codebase

## Design decisions

- Loop over six required service parameters (`http`, `llm`, `tools`, `lifecycle`, `hist_mgr`, `audit_logger`), checking each against None and raising RuntimeError with the service name if any is missing
- Keep `memory` as optional (no check for it)
- Use RuntimeError (not AssertionError) to match existing patterns in the codebase

## Alternatives considered

- Using assertions instead of RuntimeError — less explicit about what's being validated
- Adding a separate validation method called after construction — adds complexity without clear benefit

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

Add None-check loop for required services in AppServices.__init__(). Update docstring to clarify which services are optional vs required.

### Method

1. Locate lines 248-282 in `scripts/agent/context.py` (AppServices class definition)
2. Add None-check loop after parameter assignment but before returning
3. Update docstring to clarify which services are optional vs required

### Details

```python
# Before (lines 248-282):
class AppServices:
    """All required services are non-None."""
    
    def __init__(self, http=None, llm=None, tools=None, lifecycle=None,
                 hist_mgr=None, audit_logger=None, memory=None):
        self.http = http
        self.llm = llm
        self.tools = tools
        self.lifecycle = lifecycle
        self.hist_mgr = hist_mgr
        self.audit_logger = audit_logger
        self.memory = memory

# After:
class AppServices:
    """Required services (http, llm, tools, lifecycle, hist_mgr, audit_logger) must be non-None.
    Optional: memory."""
    
    def __init__(self, http=None, llm=None, tools=None, lifecycle=None,
                 hist_mgr=None, audit_logger=None, memory=None):
        self.http = http
        self.llm = llm
        self.tools = tools
        self.lifecycle = lifecycle
        self.hist_mgr = hist_mgr
        self.audit_logger = audit_logger
        self.memory = memory
        
        # Enforce invariant: required services must be present
        for _name, _svc in [("http", http), ("llm", llm), ("tools", tools),
                            ("lifecycle", lifecycle), ("hist_mgr", hist_mgr),
                            ("audit_logger", audit_logger)]:
            if _svc is None:
                raise RuntimeError(f"Required service '{_name}' is None")
```

The key change is adding a loop that checks each required service parameter against None and raises RuntimeError with the service name if any is missing. This enforces the invariant stated in the original docstring.

## Compatibility considerations

Existing callers that currently pass None for a required service will now fail at construction time rather than later at access time. This is the desired behavior per REQ-001.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original unconditional assignment if callers depend on accepting None values. This would restore the previous behavior but lose the invariant enforcement.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/context.py | Unit test — verify None rejection for required services | uv run pytest tests/agent/test_context.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Constructor raises RuntimeError when any required service is None (REQ-001)
- [ ] Test verifies error message includes the service name (REQ-002)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to the service initialization order in factory.py
- Changes to the type annotations
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
- **Requirement ID**: REQ-001, REQ-004
- **Source issue**: issues/20261004-143009_as010_no_required_validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182817_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-195847
- **Related target files**: scripts/agent/context.py
