## Goal
Cite every newly registered ADR-008-targeted Known Issue in ADR-008 `## Known Deviations` so the reverse sync check passes (REQ-004, AC-4). This is a conditional row: conversion re-verification found no new ADR-008-targeted candidate, so the expected outcome is a reported no-op.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Conversion re-verification 2026-11-12 (plan Background): the only live Phase 3 candidate is the governance_02 Part 4 empty-token contradiction (Target: governance_02, not ADR-008); the Dry Run versus WAL gap is already registered as SHARED-001 and already cited in this ADR.
- Procedure 01 (`implementations/20261112-062831_01_docs_00_governance_governance_03_issue-and-uncertainty-management.md.md`) decides whether any new ADR-008-targeted Part 1 entry is registered.

## Design decisions
- Row stays in scope as the reverse-check half of REQ-004 (GV-022 check 3); it becomes a real edit only if procedure 01 registers a Part 1 entry whose `Target` is ADR-008.

## Alternatives considered
N/A: conditional row fixed by the plan design; removing it would drop the GV-022 reverse-check coverage.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. After procedure 01 Phase 3: if any newly registered Part 1 Known Issue has `Target` ADR-008, append one citation bullet per such ID to the `## Known Deviations` section of `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`, matching the existing SHARED-001/SHARED-002 citation format and pointing to `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1.
2. If none is registered, make no edit and report that this row needed no edit (with the refuted-candidate list from procedure 01).

### Method
Direct Markdown edit appended after the existing SHARED-002 bullet; leave the existing bullets untouched.

### Details
- The existing section in `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` (lines 348-351) already cites SHARED-001 and SHARED-002, added by the landed adrrev009 procedures; the plan's original "Not applicable" evidence is superseded.
- Citation wording per `tools/check_known_deviation_sync.py`: `**Known Issue:** {ID} — {one-line gap}. ... See \`docs/00_governance/governance_03_issue-and-uncertainty-management.md\` Part 1.`

## Compatibility considerations
N/A: `## Known Deviations` is the only section touched; sibling Plans edit other ADR-008 sections (overlap check judged compatible).

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_known_deviation_sync.py` — Pass; no finding for any registered ADR-008-targeted entry (AC-4)
- `uv run python tools/check_adr_structure.py` — Pass

## Completion criteria
Either (a) every newly registered ADR-008-targeted Known Issue is cited in `## Known Deviations` and `check_known_deviation_sync.py` reports no finding, or (b) no new entry was registered and the no-op outcome is reported with the refuted-candidate evidence.

## Out of Scope
The Part 1 registration itself (procedure 01), all ADR-008 sections other than `## Known Deviations`, and fixing the underlying gaps (sibling Plans).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append citations for newly registered ADR-008-targeted Known Issues, or report the no-op (REQ-004) | Pending | — | — | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure; no new ADR-008-targeted candidate is expected |
| 2 | Run the documentation checkers in the Validation plan | Pending | — | — | Gated: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md phase all - only live Phase 3 candidate (MCP empty-token documentation contradiction (mcp_02_02 and mcp_06_14 vs scripts/mcp_servers/server.py), REQ-003) is expected to be landed or updated by adrrev011's procedure |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261109-113054_adrrev012_adr-approval-ledger.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095703_adrrev012_adr-approval-ledger.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-062831
- **Related target files**: docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md
