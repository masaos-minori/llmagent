## Goal

Add the approval provenance fields to `ToolApprovalEvent` without breaking existing constructions (REQ-007).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `scripts/agent/shared/models.py`; assertions live in the approval test row.

## Assumptions

- Verified: `ToolApprovalEvent` is a frozen dataclass whose last field is `idempotency_key` (`scripts/agent/shared/models.py:13-28`); new fields must be defaulted and come after it.

## Design decisions

- Add `request_id`, `preview_source`, and `fallback_reason`, each a string defaulting to empty.

## Alternatives considered

N/A: three defaulted fields.

## Implementation
### Target file
`scripts/agent/shared/models.py`

### Procedure
1. Append the three fields after `idempotency_key` with one-line comments; no answer-text field is added.

### Method
Dataclass field additions only.

### Details
- Field order keeps positional construction in existing code and tests valid.

## Compatibility considerations

Serialized audit lines gain three keys; consumers that read known keys are unaffected.

## Security considerations

The event deliberately has no field for the operator's answer.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent -k "audit or approval" -q`
- `uv run ruff check scripts/agent/shared/models.py && uv run mypy scripts/agent/shared/models.py`

## Completion criteria

- The three fields exist with empty defaults; no existing construction breaks.

## Out of Scope

Writing the fields (audit row) and filling them (approval row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`); assertions are in the approval test row | Pending | — | — | |

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
- **Requirement ID**: `REQ-007` (audit event carries request id, preview source, fallback reason)
- **Source issue**: issues/20261119-145259_cliplc001_repl-input-controller.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261122-210208_cliplc001_repl-input-controller.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261122-210644
- **Related target files**: `scripts/agent/shared/models.py`
