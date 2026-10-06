## Goal

Include remediation steps in the FATAL error message raised by `StartupOrchestrator._check_services()`, matching the behavior already present in `startup_reporter.py`.

## Scope

- Modify `scripts/agent/startup.py`: include remediation in FATAL error message
- Read `scripts/agent/startup_reporter.py`: understand existing remediation display format

## Assumptions

- The `StartupOutcome` object has a `remediation` attribute (confirmed by issue statement)
- The format should match `startup_reporter.py`'s existing remediation display
- External tooling currently parses the error message and needs to handle the new format

## Design decisions

- Replace the simple `"; ".join(pipeline.fatal_messages())` with a loop over `pipeline.outcomes` that builds a formatted string including both the message and remediation for each FATAL outcome
- Match the format used in `startup_reporter.py` exactly
- Use a structured format: "Message\nRemediation: ..." for each FATAL outcome

## Alternatives considered

- Adding a separate method to build the error message — over-engineering for this use case
- Using JSON formatting — breaks readability for users but preserves structure for tooling

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

Replace `"; ".join(pipeline.fatal_messages())` with structured format including remediation.

### Method

1. Locate lines 115-121 in `scripts/agent/startup.py` (fatal_messages() call)
2. Replace the simple join with a loop that includes remediation text

### Details

```python
# Before (lines 115-121):
def _check_services(self, pipeline: StartupValidationPipeline) -> None:
    fatal = pipeline.fatal_messages()
    if fatal:
        raise RuntimeError("; ".join(fatal))

# After:
def _check_services(self, pipeline: StartupValidationPipeline) -> None:
    fatal_outcomes = [o for o in pipeline.outcomes if o.is_fatal]
    if fatal_outcomes:
        parts = []
        for outcome in fatal_outcomes:
            part = f"{outcome.message}"
            if hasattr(outcome, 'remediation') and outcome.remediation:
                part += f"\nRemediation: {outcome.remediation}"
            parts.append(part)
        raise RuntimeError("\n\n".join(parts))
```

The key change is replacing the simple `"; ".join(pipeline.fatal_messages())` with a loop over `pipeline.outcomes` that builds a formatted string including both the message and remediation for each FATAL outcome, matching the format in `startup_reporter.py`.

## Compatibility considerations

This change may affect external tooling that parses the FATAL error message. However, the new format is more informative and follows the same pattern as `startup_reporter.py`.

## Security considerations

N/A: No security impact.

## Rollback considerations

Revert to the original `"; ".join(pipeline.fatal_messages())` if external tooling breaks due to the changed format. This would restore the previous behavior but lose remediation visibility.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/startup.py | Unit test — verify FATAL error message includes remediation | uv run pytest tests/agent/test_startup.py | New tests pass, existing tests pass |

## Completion criteria

- [ ] Error message includes remediation steps for each FATAL outcome (REQ-001)
- [ ] Test verifies error message contains remediation text (REQ-002)
- [ ] Formatting matches existing display format (REQ-003)
- [ ] All new tests pass when run individually

## Out of scope

- Changes to the validation pipeline itself
- Changes to the remediation content generation
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
- **Source issue**: issues/20261004-143012_so013_missing_remediation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182820_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261004-200157
- **Related target files**: scripts/agent/startup.py
