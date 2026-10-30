# Implementation Procedure: test_transport_dto.py hint contract tests

## Goal

Lock the `DynamicAvailabilityHint` (new) / `ToolCallResult.availability_hint` contract with unit
tests in `tests/shared/test_transport_dto.py` (REQ-001, REQ-002).

## Scope

**In scope:**
- `tests/shared/test_transport_dto.py`: new test class(es) for the hint field.

**Out of scope:**
- Producer-side behavior (row 09 covers the invoker), guard behavior (row 10).

## Assumptions
- Verified at HEAD `124e340b4`: the file exists and covers `from_transport` error_type
  classification only; `ToolCallResult` is frozen with 6 fields
  (`transport_dto.py:8-20`). Test-first: these tests fail until row 01 lands.

## Design decisions
- Characterization first: existing `from_transport` tests stay untouched and must stay
  green after row 01 (they are the default-shape lock: `availability_hint is None` on
  every legacy construction).
- New assertions: explicit-keyword construction with a hint round-trips; frozen
  semantics (`dataclasses.replace` works, direct assignment raises); `reason` accepts
  exactly the two literal values; `retry_after_seconds` (new) accepts `None` and ints;
  `server_key` default `""` behavior unchanged.

## Alternatives considered
- Schema/JSON snapshot testing of the DTO: rejected — field-level assertions are the
  repo's existing style for DTOs and keep the advisory-only shape reviewable.

## Implementation
### Target file
`tests/shared/test_transport_dto.py`

### Procedure
1. Keep every existing test byte-identical.
2. Add `TestAvailabilityHint` (new) covering the decisions above.

### Method
- Pure unit tests, no fixtures or mocks needed (DTO has no behavior).

### Details
- Import `DynamicAvailabilityHint` (new) and `McpServerHealthState` in the test module.

## Compatibility considerations
- None beyond the existing suite: test-only file.

## Security considerations
- Not applicable (test-only).

## Rollback considerations
- Remove the new class to revert; existing tests are never edited.

## Validation plan
- `uv run pytest tests/shared/test_transport_dto.py -v` — fails before row 01, green
  after; ruff clean.

## Completion criteria
- New hint-contract tests exist and pass after row 01; every pre-existing test unchanged
  and green.

## Out of Scope
- Row 01 implementation itself, invoker/guard tests (rows 09-11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `TestAvailabilityHint` (new) (fails before row 01 lands) | Pending | — | — | |
| 2 | Confirm existing tests byte-identical and green after row 01 | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261029-104507_toolhint001_dynamic-tool-health-hints.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-083821
- **Related target files**: `tests/shared/test_transport_dto.py`
