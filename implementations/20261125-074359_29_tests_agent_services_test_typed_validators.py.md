## Goal

Cover the validators as a delegating layer: the field path carried in the error and the bool-for-number
rejection must still hold after the implementation moves to the shared primitives (REQ-001, shared strict
type rules; REQ-011, structured config error).

## Scope
**Release unit**: R1-strict-primitives

## Assumptions
- The current tests pin the error text; the delegating layer keeps the wording shape through the shared
  `FieldRule` vocabulary, so the existing assertions stay valid where the rule name is unchanged.
- The primitives are covered by row 25; this file covers only the delegating layer, not the primitives.

## Design decisions
- Add assertions for the field path in the message, which the current tests do not check.
- Keep the existing coercion-tolerant cases only where the behavior is unchanged; a case that asserted a
  coerced value is retargeted to a rejection.

## Alternatives considered
- Deleting these tests in favor of the primitive tests — rejected: the delegation itself is the contract
  the startup builders depend on.

## Implementation
### Target file
`tests/agent/services/test_typed_validators.py`

### Procedure

### Method
- Assert each `_get_*` raises with the field path and the rule name.
- Assert `bool` is rejected by `_get_int` and `_get_float`.
- Assert the non-empty variants reject an empty value when `allow_empty` is false.

### Details
- No new test class is introduced; the existing classes gain the field-path assertions.

## Compatibility considerations
- Blast radius: this file is the only pin on the delegating layer's error text.

## Security considerations
- N/A: the tests assert message structure, not output.

## Rollback considerations
- Revert the Phase 1 commit.

## Validation plan
- `uv run pytest tests/agent/services/test_typed_validators.py -q`

## Completion criteria
- Every delegating function has a case that shows the field path reaches the error, and no test asserts a
  message containing a raw value.

## Out of Scope
- The primitive behavior (row 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (shared strict type rules), REQ-011 (structured config error); AC-1
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `tests/agent/services/test_typed_validators.py`
