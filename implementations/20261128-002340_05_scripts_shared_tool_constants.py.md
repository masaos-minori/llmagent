# Implementation Procedure — scripts/shared/tool_constants.py

## Goal

Remove `index_paths` and `refresh_index` from `RETRYABLE_TOOLS` so the reference data matches the new
`never` declarations (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirements: REQ-005. Acceptance criterion: AC-3.

## Assumptions
- Lightweight fill: reference data only, one constant, no public-contract, persistence, or security
  impact.
- The declared `retry_policy` field is the authority (the comment at lines 177-184); this set only
  detects drift, so removing the two entries is the whole change.
- Overlap: this file is not targeted by another Frozen Plan.

## Design decisions
- No new reference set and no comment rewrite: the existing comment already states the set is
  reference data.

## Alternatives considered
- N/A: single-constant change; the alternative (keeping the entries) would leave the drift check failing.

## Implementation
### Target file
`scripts/shared/tool_constants.py`

### Procedure
- Delete the `"index_paths"` and `"refresh_index"` entries (lines 202-203) from `RETRYABLE_TOOLS`.

### Method
- N/A: no logic change.

### Details
- The `# mdq server (mdq)` comment block becomes empty and is removed with the entries.

## Compatibility considerations
- Consumers are `scripts/shared/tool_metadata.py` (unchanged), `tests/shared/test_tool_constants.py`
  (this Plan's row 11), and the generated reference table checked by
  `uv run python tools/generate_reference_table.py --check`.

## Security considerations
- N/A: reference data only.

## Rollback considerations
- N/A: revert the commit; must roll back together with row 4.

## Validation plan
- `uv run pytest tests/shared/test_tool_constants.py`
- `uv run python tools/generate_reference_table.py --check`, then `uv run pytest`.

## Completion criteria
- The declarations and the reference data agree (AC-3).

## Out of Scope
- The declarations (row 4); the drift test (row 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Tests are row 11's own document |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | `docs/22_mcp/mcp_04_04_mdq.md` (row 13) |

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261119-142127_mdqmcp005_mdq-transaction-atomicity.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-171503_mdqmcp005_mdq-transaction-atomicity.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-002340
- **Related target files**: `scripts/shared/tool_constants.py`
