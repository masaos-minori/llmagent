## Goal

Add the optional call-identity keys to the `transport_failure` diagnostic record (REQ-005, the record cannot be joined to the audit line or the state row today).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Additive JSON keys only in the `content` blob; no schema, DDL, or migration change (Plan Design, persisted-schema check).
- The values are supplied by the row 6 bridge; the parameters default to `""` so the old call shape keeps working.

## Design decisions

- Four optional keyword parameters (`call_id`, `request_id`, `task_id`, `turn_id`), each `str = ""`, serialized only as plain keys in the existing `content` dict.
- The existing positional signature (`session_id, tool_name, server_key, error_msg`) is unchanged, so current callers and tests keep working.

## Alternatives considered

N/A: single-function change with no contract impact.

## Implementation
### Target file
`scripts/agent/diagnostic_store.py`
### Procedure
Extend `save_transport_failure` with the optional id parameters.

### Method
- Add keyword-only parameters `call_id: str = ""`, `request_id: str = ""`, `task_id: str = ""`, `turn_id: str = ""` to `save_transport_failure` (line 259).
- Add the four keys to the `content` dict built at line 267; existing keys stay first.

### Details
- Only what the Plan's Requirement text does not already state: the keys are written even when empty, so the record shape is stable for readers.

### Companion test files
- `tests/agent/test_diagnostic_store.py`
  - Procedure: cover the new optional keys and the old-call-shape compatibility (REQ-005, REQ-006; the existing `test_save_transport_failure` at line 197 stays passing).
  - Validation: `uv run pytest tests/agent/test_diagnostic_store.py`

## Compatibility considerations

Records written before the change lack the keys and remain parseable (REQ-006, AC-4).

## Security considerations

N/A: the keys carry identifiers; the existing `error` free-text redaction question stays with the redaction Issue (UNK-03).

## Rollback considerations

N/A: revert the commit; the keys are additive.

## Validation plan

- `uv run pytest tests/agent/test_diagnostic_store.py`
- `uv run mypy scripts/agent/diagnostic_store.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- A call with the new parameters produces a record containing the five identity keys (AC-5).
- A call with the old shape produces the same record as before plus the empty keys.

## Out of Scope

- Redaction of the `error` text (UNK-03, redaction Issue).
- Supplying the values (row 6 procedure).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add the companion test per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (diagnostic record gains `call_id`, `request_id`, `task_id`, `turn_id`)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/agent/diagnostic_store.py`, `tests/agent/test_diagnostic_store.py`
