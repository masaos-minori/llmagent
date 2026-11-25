## Goal

Create the shared write-outcome vocabulary and write-audit field contract (REQ-007) that the GitHub code uses now and the Git, File, and CI/CD servers reuse later.

## Scope
**Release unit**: R1-github-write-safety

## Assumptions

- `scripts/shared/` is an import-linter leaf: the module imports only the standard library.
- The dispatcher's row states and acquisition states already contain `outcome_unknown`; this module defines the write-result vocabulary only and adds no ledger status (no persisted-schema change).
- Code docstrings and comments must not carry REQ markers (the repository checks that); cite behavior, not Plan ids.

## Design decisions

- The vocabulary is two string constants plus a `Literal`, and one frozen set naming the outcomes that must never be retried automatically.
- The audit contract is a pure function returning the ordered key-value fields of one audit record, so every server writes the same identifiers in the same order.

## Alternatives considered

A dataclass for the audit record was rejected: servers format records differently (`key=value` text versus structured logs), so a field mapping is the common denominator.

## Implementation
### Target file
`scripts/shared/write_outcome.py` (new)

### Procedure
Create the module with the vocabulary and the field builder.

### Method
- Define `WriteOutcome` (new) as `Literal["outcome_unknown", "applied_audit_failed"]`, with `OUTCOME_UNKNOWN` (new) and `APPLIED_AUDIT_FAILED` (new) as the matching string constants.
- Define `NO_AUTO_RETRY_OUTCOMES` (new) as a `frozenset` of both values: neither is retried automatically.
- Define `build_write_audit_fields` (new) taking `(op, phase, session_id, request_id, call_id)` and returning a `dict[str, str]` with keys `op`, `phase` (`intent` or `completion`), `session`, `request`, `call` in that order; empty identifiers are rendered as `-`; any other phase raises `ValueError`.

### Details
- Module docstring first line: `scripts/shared/write_outcome.py — ...` (docstring-format gate).
- The function never accepts or returns payload text.

### Companion test files
- `tests/shared/test_write_outcome.py` (new)
  - Procedure: Add cases: both constants and the frozen set; the field order; empty identifiers render as `-`; an unknown phase raises `ValueError`.
  - Validation: `uv run pytest tests/shared/test_write_outcome.py`

## Compatibility considerations

New module and names only.

## Security considerations

The field builder takes identifiers only, so a payload cannot enter an audit record through it.

## Rollback considerations

Delete the module and its test before the GitHub procedures land; afterwards revert the release unit together.

## Validation plan

- `uv run pytest tests/shared/test_write_outcome.py`
- `uv run mypy scripts/shared/write_outcome.py`
- `uv run ruff check` and `uv run ruff format`
- `uv run python tools/run_validation_gates.py` (module docstring and size gates)

## Completion criteria

- The vocabulary, the no-retry set, and the field builder exist and import only the standard library.

## Out of Scope

- Using the contract in Git, File, or CI/CD servers (their own work items).
- A ledger status for these outcomes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261125-183206 | 20261125-183206 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261125-183206 | 20261125-183206 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-183206 | 20261125-183206 | row3: targeted tests pass (6 passed); gates pass |

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
- **Requirement ID**: REQ-007
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `scripts/shared/write_outcome.py`, `tests/shared/test_write_outcome.py`