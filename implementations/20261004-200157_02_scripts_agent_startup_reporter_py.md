## Goal

Verify that `startup_reporter.py`'s existing remediation display format is compatible with the proposed format in startup.py.

## Scope

- Read `scripts/agent/startup_reporter.py`: understand existing remediation display format

## Assumptions

- The `StartupOutcome` object has a `remediation` attribute
- The format in `startup_reporter.py` uses "\nRemediation: ..." style formatting

## Design decisions

- No modification needed — this is a read-only verification step
- If the format differs significantly from what we're implementing, report as Blocked

## Alternatives considered

- Modifying `startup_reporter.py` to align formats — unnecessary if formats are already consistent
- Adding a shared formatting utility — over-engineering for this use case

## Implementation

### Target file

`scripts/agent/startup_reporter.py`

### Procedure

Read and verify the existing remediation display format in startup_reporter.py.

### Method

1. Locate lines 66-67 in `scripts/agent/startup_reporter.py` (remediation display)
2. Verify the format matches the proposed format in startup.py

### Details

```python
# Expected structure in scripts/agent/startup_reporter.py around line 66-67:
for outcome in self._outcomes:
    if outcome.is_fatal:
        result["status"] = "unavailable"
        result["reason"] = outcome.message
        if outcome.remediation:
            result["remediation"] = outcome.remediation
```

If the format uses "\nRemediation: ..." style, proceed to the next step. Otherwise, report as Blocked.

## Compatibility considerations

N/A: This is a read-only verification step.

## Security considerations

N/A: No security impact.

## Rollback considerations

N/A: No changes made.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup_reporter.py | Verification — confirm remediation display format | Manual inspection | Format confirmed |

## Completion criteria

- [ ] Existing remediation display format verified and compatible with proposed format

## Out of scope

- Modifying `startup_reporter.py` or its methods
- Creating new test file (handled in separate document)

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261004-143012_so013_missing_remediation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182820_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-200157
- **Related target files**: scripts/agent/startup_reporter.py
