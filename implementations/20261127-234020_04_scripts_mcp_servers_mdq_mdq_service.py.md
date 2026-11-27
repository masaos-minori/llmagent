# Implementation Procedure — scripts/mcp_servers/mdq/mdq_service.py

## Goal

Outline inspects the filesystem and reports the shared stale state, and the stale count is computed
from the state set (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit (the Plan lists no release units)

Requirement: REQ-004 (outline reports the shared state). Acceptance criterion: AC-3.

## Assumptions
- Full form: this row changes the outline read path's public output.
- The state vocabulary and the state function come from seq 03; this document uses them and does
  not redefine them.
- `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` is this row's companion.

## Design decisions
- `_check_stale_document()` (line 237) becomes the filesystem-aware state reader: it stats the
  path and calls `classify_stale_state()` (new) instead of comparing stored columns only.
- The stale count in `stats()` (line 343) counts documents in the stale state through the
  redesigned `STALE_SQL_CONDITION`, so health and outline read the same definition.

## Alternatives considered
- Keep the stored-columns comparison and add a filesystem check only for the missing state:
  rejected, because REQ-004 requires one shared definition, not two readers.

## Implementation
### Target file
`scripts/mcp_servers/mdq/mdq_service.py`

### Procedure
- In `_check_stale_document()` (line 237), replace the stored-columns comparison at line 249 with
  the state function plus a `stat()` of the path; a path that no longer exists is the missing
  state.
- Keep `outline()` (line 180) as the caller; the returned warning carries the state name.

### Method
- The filesystem read is done once per outline call, on the path already resolved by the
  allowlist check; no additional database query is added.

### Details
- The plan's line 249 citation is the `is_stale()` call inside `_check_stale_document()`, which
  `outline()` calls; the guard that returns nothing when the document row is absent becomes the
  inconsistent-state branch.

### Companion test files
- `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`
  - Procedure: orphan chunks without a document row become the explicit inconsistent state, and a
    deleted file becomes the missing state; the existing pre-FK orphan guard (lines 49-51) keeps
    its fixture and gains the state assertion.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` — the two
    states are explicit in the response.

## Compatibility considerations
- `OutlineResponse.stale_warning` wording changes to the state name; the Plan records the response
  shape as additive, so existing consumers that only check for a warning keep working.

## Security considerations
- N/A: the path is already allowlist-checked before the stat call.

## Rollback considerations
- N/A: revert the commit; the state function it calls belongs to seq 03.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`
- `uv run python tools/run_validation_gates.py`, then `uv run pytest`.

## Completion criteria
- The missing and inconsistent states are explicit in the outline output (AC-3), and the stale
  count comes from the same definition health uses.

## Out of Scope
- Health reporting (seq 05); the state-set definition itself (seq 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Companion `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` |
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
- **Requirement ID**: REQ-004 (outline reports the shared stale state)
- **Source issue**: `issues/20261119-142126_mdqmcp004_mdq-file-identity-stale.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-170412_mdqmcp004_mdq-file-identity-stale.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-234020
- **Related target files**: `scripts/mcp_servers/mdq/mdq_service.py`, `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py`
