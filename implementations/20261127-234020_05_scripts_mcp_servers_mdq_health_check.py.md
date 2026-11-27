# Implementation Procedure — scripts/mcp_servers/mdq/health_check.py

## Goal

Health reports the shared stale-state set as per-state counts while `stale_document_count` keeps its
current meaning as the count of documents in the stale state (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirement: REQ-004 (health and outline use the same state definitions). Acceptance criterion:
AC-3.

## Assumptions
- Full form: this row changes the `/health` response shape.
- The state vocabulary and the state function come from seq 03; this document uses them and does
  not redefine them.
- `tests/mcp_servers/mdq/test_mdq_health_stale.py` is this row's companion.

## Design decisions
- `_check_stale_documents()` (line 48) becomes the state-count function and returns the per-state
  counts; the response key `stale_document_count` (line 110) stays an integer count of documents
  in the stale state.
- The per-state counts are published under a new key `stale_state_counts` (new), additive to the
  existing response, so no existing key changes type.

## Alternatives considered
- Replace `stale_document_count` with the state map: rejected, because the Plan preserves that key
  as the stale-state count and existing consumers read it.

## Implementation
### Target file
`scripts/mcp_servers/mdq/health_check.py`

### Procedure
- Rewrite `_check_stale_documents()` (line 48) to count per state through the redesigned
  `STALE_SQL_CONDITION` and return the state counts.
- Add `stale_state_counts` (new) to the details dict at line 110 and keep
  `stale_document_count` as the stale-state count.

### Method
- The function keeps returning `None` when the `documents` table is missing, so the schema-error
  path and the existing key-presence behavior are unchanged.

### Details
- Per-state counts are additive: the sum of the state counts equals the number of document rows,
  plus the orphan-chunk count for the inconsistent state.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_health_stale.py`
  - Procedure: move the fixture DDLs onto the new canonical columns (lines 24-35 and 36-55),
    assert the per-state counts, and keep the preserved `stale_document_count` semantics asserted
    at line 105; the corrupt-database case keeps its `None` expectation.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_health_stale.py` — per-state counts
    and the preserved key.

## Compatibility considerations
- The response gains one key; `tests/mcp_servers/mdq/test_mdq_health_endpoint.py` (seq 13) and
  `tests/mcp_servers/mdq/test_mdq_security_validation.py` (seq 21) are the consumers that pin the
  existing keys and fixture shape.

## Security considerations
- N/A: counts only; no path or value is exposed beyond the existing keys.

## Rollback considerations
- N/A: revert the commit; the state counts depend on the seq 01 columns and the seq 03 vocabulary.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_health_stale.py tests/mcp_servers/mdq/test_mdq_health_endpoint.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- Health publishes per-state counts and `stale_document_count` remains the stale-state count
  (AC-3), from the same definitions outline uses.

## Out of Scope
- The state-set definition (seq 03); the outline reader (seq 04); readiness reporting added by the
  mdqmcp001 plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_health_stale.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (seq 18) |

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
- **Requirement ID**: REQ-004 (health reports the shared state set)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `scripts/mcp_servers/mdq/health_check.py`, `tests/mcp_servers/mdq/test_mdq_health_stale.py`
