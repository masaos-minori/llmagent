## Goal

Update the dedup-degradation observability row of `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md` to the new warning taxonomy (lease conflicts, `reconciliation_required`, replaced/legacy refusals) (REQ-006, REQ-012; AC-11).

## Scope
**Release unit**: docs-sync

## Assumptions
- Row 02 has landed: the structured `logger.warning` markers exist; ADR-004 MCP-002 (write-failure warning-only) is unchanged.
- Current row (verified 2026-11-21, :30): "Dedup Protection Degraded (MCP dedup store) | Dispatcher WARNING-level log on any of: dedup store unavailable at init, dedup lookup failure, dedup store write failure" — the lookup-failure wording dies with the `lookup` API.

## Design decisions
- Keep the row's table shape (condition / signal / payload) and only update the trigger list and the referenced decision-table link (db_03_07, row 17).

## Alternatives considered
- N/A: documentation reconciliation of frozen contract text.

## Implementation
### Target file
`docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`
### Procedure
Rewrite the observability row's trigger list.
### Method
- New triggers: store opened in `lost`/`replaced`/`legacy_or_unverified`/`schema_mismatch` (refusal or degraded marker), lease-conflict (`DedupLeaseConflict`) warnings, `reconciliation_required` classifications, and the retained store-write-failure warning-only case.
- Keep the tool-audit payload note (the payload carries the new `dedup` snapshot component unchanged, row 03).
### Details
- `lookup`-failure wording must disappear (API removed by row 01).

## Compatibility considerations
- Operators' alert expectations shift only in trigger vocabulary; severity stays WARNING.

## Security considerations
- N/A: prose.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py` (routing.md docs gate).

## Completion criteria
- AC-11: the row documents the new warning set and no `lookup`-era wording remains.

## Out of Scope
- The logging implementation (row 02), other observability rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the doc per Implementation > Method | Pending | — | — | |
| 2 | Run the docs checkers (routing.md Tools) | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-012
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `docs/23_agent/agent_10_05_operations-and-observability-monitoring.md`
