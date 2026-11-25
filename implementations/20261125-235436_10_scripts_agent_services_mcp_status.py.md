## Goal

Map the new lifecycle states and retained snapshots into the `/mcp status` row so unconfirmed processes are shown (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 5 is outside R3-ownership)

## Assumptions
- The new states come from row 01; the retained snapshot and its outcome field from rows 03 and 09.

## Design decisions
- Extend the status mapping beyond the current `FAILED`-only restart recommendation (`:146-151`): `EXIT_UNCONFIRMED` and `SIGNAL_NOT_DELIVERED` rows show the retained process with its outcome.

## Alternatives considered
- N/A: no alternative for the display mapping; the Plan fixes the semantics.

## Implementation
### Target file
`scripts/agent/services/mcp_status.py`

### Procedure
Extend the status-row build (`:144-152`) to read the outcome from the snapshot and map the new states to availability and restart recommendation.

### Method
Add state branches to the existing mapping; no new service or API.

### Details
- Keep the pinned stopped-state display green (`tests/agent/commands/test_cmd_mcp.py:242`, Plan predictable-fallout check).

### Companion test files
- `tests/agent/commands/test_cmd_mcp.py`
  - Procedure: `/mcp status` display test for an unconfirmed retained process (REQ-011 defect-pinning set, Phase 1).
  - Validation: `uv run pytest tests/agent/commands/test_cmd_mcp.py`.

## Compatibility considerations
- Command output tests that assert existing rows must stay green.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Integration: unconfirmed process named in `/mcp status` — `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/commands/test_cmd_mcp.py` (AC-1).

## Completion criteria
- A retained unconfirmed record appears in the status output with its pid, pgid, and outcome; existing status rows unchanged.

## Out of Scope
- The snapshot field (row 09), the record retention itself (rows 03-05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
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
- **Requirement ID**: REQ-009 (show unconfirmed processes in `/mcp status`)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/services/mcp_status.py`, `tests/agent/commands/test_cmd_mcp.py`
