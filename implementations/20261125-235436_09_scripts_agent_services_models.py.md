## Goal

Add the defaulted `termination_outcome` (new) field to `ProcessInfoSnapshot` so snapshots can report an unconfirmed retained process (REQ-009).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 5 is outside R3-ownership)

## Assumptions
- The field is defaulted (`str | None = None`), compatible with the 19 importers (grimp, Plan Step 5).

## Design decisions
- Additive field only: no field removed or renamed (Plan Risks).

## Alternatives considered
- N/A: no alternative for an additive dataclass field.

## Implementation
### Target file
`scripts/agent/services/models.py`

### Procedure
Add `termination_outcome` (new) (`str | None = None`) to `ProcessInfoSnapshot` (`:38-47`).

### Method
One field; the value is the `TerminationOutcome` enum value string, set by `_build_snapshot` (row 03).

### Details
- The field stays `str | None` rather than the enum type to keep `services.models` free of the agent-lifecycle import (import-layer contract, `skills/DESIGN.md` Shared Vocabulary).

## Compatibility considerations
- Defaulted field: existing constructions are unaffected.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Integration: retained snapshot visible in status output — `uv run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/commands/test_cmd_mcp.py` (REQ-009).

## Completion criteria
- The field exists with a default, `_build_snapshot` populates it for retained records, and the integration tests show it.

## Out of Scope
- The status-row mapping (row 10), the snapshot construction (row 03).

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
- **Requirement ID**: REQ-009 (unconfirmed processes visible in `/mcp status`)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/services/models.py`
