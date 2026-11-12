## Goal
Add `rag-pipeline-mcp` to ADR-008's Target components, which its recovery table already names (`REQ-006`, `REQ-008` / `AC-6`, `AC-8`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The `Target components` line (about line 143) lists `DbConfig`, `SQLiteHelper`, `create_schema()`, `db/recovery.py`, `db/maintenance.py`; the recovery table names rag-pipeline-mcp at its stop-scope and restart rows (checked).
- `adrrev009` (landed) edited Decision Detail #7 and Known Deviations only, so the line is untouched; the PAUSED banner of this Plan was stale and is removed in Step 3a.
- Baseline (Step 3a, 2026-11-12): `check_docs_structure.py` already reports ADR-004, ADR-008, and `deployment_01` over their ceilings (pre-existing, unrelated to this Plan).

## Design decisions
- One clause appended to the existing line.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`

### Procedure
1. Append `rag-pipeline-mcp` to the Target components line.
2. Append a `Current Decision Approval (pending)` line.

### Method
- New value: `... db/recovery.py`, `db/maintenance.py`, and the `rag-pipeline-mcp` service that opens `rag.sqlite``.
- Approval line: approver, date, scope 不明; tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); no approval or reviewer name is written (UNK-05).
- Size gate: `tools/check_docs_structure.py` records a per-file ceiling equal to the accepted size, so any growth of this document fails `check_docs_structure.py`. The ceiling table is outside this Plan's target files; re-recording it follows the existing ceiling re-record chore (`plans/done` / `implementations` docsize series). Report the new size; do not edit the tool here (non-blocking `Needs confirmation`).
- This ADR is already over its ceiling (36197 of 34206); the ceiling re-record chore covers it.

## Compatibility considerations
N/A: documentation-only change; no code, config, or schema impact.

## Security considerations
N/A: no authorization, secret, or trust-boundary change.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_adr_structure.py`, `check_adr_invariant_matrix.py`, `check_adr_reference.py`, `check_adr_authority.py`, `check_adr_preservation.py` (only intended, explained changes).
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_japanese.py` — pass.

## Completion criteria
- Target components include rag-pipeline-mcp; a marked pending approval line exists.

## Out of Scope
- Known Deviations and Decision Detail #7 (adrrev009, landed); the Status-cell shortening.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers per Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` / `REQ-008` — Target components include rag-pipeline-mcp; pending approval
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md`
