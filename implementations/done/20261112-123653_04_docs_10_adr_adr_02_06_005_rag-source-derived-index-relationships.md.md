## Goal
Replace ADR-005's restated FTS text-selection rule (Decision 8 and the matching Implementation Note) with a reference to ADR-009, with a pending approval record (`REQ-001`, `REQ-008` / `AC-1`, `AC-8`).

## Scope
**Release unit**: authority-model

## Assumptions
- Decision 8 (about line 74) says synchronization and manual rebuilds use `COALESCE(normalized_content, content)`, and the Implementation Note (about line 245) repeats it for `RagMaintenanceService.rebuild_fts()`; ADR-009 INV-03 and INV-07 own the rule (checked).
- Overlap: adrrev013 (Decisions 10 and 11, startup paragraph) is compatible; this edit touches Decision 8 only.
- The registered supplemental limit is `FTS synchronization and rebuild operations only` (row 01).

## Design decisions
- Keep the operational statement (rebuild uses the same rule as the triggers) but cite ADR-009 as the owner instead of spelling out the expression.

## Alternatives considered
N/A: the Plan fixes the approach for this row.

## Implementation
### Target file
`docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`

### Procedure
1. Rewrite Decision 8 to reference ADR-009 INV-03 and INV-07.
2. Rewrite the `rebuild_fts()` Implementation Note the same way.
3. Append a `Current Decision Approval (pending)` line.

### Method
- Decision 8: `FTS5 synchronization and manual rebuilds follow the text-selection rule owned by ADR-009 (INV-03, INV-07); this ADR owns only the synchronization and rebuild operations.`
- Note: `RagMaintenanceService.rebuild_fts()` regenerates `chunks_fts` under the ADR-009 text-selection rule, the same as the triggers.
- Approval line: approver, date, scope 不明; tracked by adrrev012.

### Details
- Each decision-text edit gets a clearly marked `Current Decision Approval (pending)` line in the ADR's Approval Record (approver, date, and scope `不明`), tracked by the approval-ledger Plan (adrrev012); no approval or reviewer name is written (UNK-05).
- Do not remove the ADR-009 related entry or change Decision numbering.

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
- ADR-005 no longer restates the expression; it cites ADR-009; a marked pending approval line exists.

## Out of Scope
- ADR-009's text; Decisions 10 and 11 (adrrev013).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261112 | 20261112 | implemented per Procedure/Method/Decision 8 + rebuild_fts() Note -> ADR-009 (INV-03,INV-07), Amendment subsection + pending approval line added |
| 2 | Run the documentation checkers per Validation plan | Completed | 20261112 | 20261112 | all checkers pass (preservation: Approval ERROR + Decision WARNING are the intended explained changes) |

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
- **Requirement ID**: `REQ-001` / `REQ-008` — ADR-005 references ADR-009 for the FTS text-selection rule
- **Source issue**: issues/20261109-113248_adrrev016_adr-authority-format.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-104605_adrrev016_adr-authority-format.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-123653
- **Related target files**: `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md`
