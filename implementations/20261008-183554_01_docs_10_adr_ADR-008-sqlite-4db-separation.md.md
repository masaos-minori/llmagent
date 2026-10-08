## Goal
Record mdq.sqlite as a derived store, fix the Recovery Policy Matrix and the migration constraint, and remove the unrelated Known Deviation (REQ-001 to REQ-007 of the Plan).

## Scope
- Only `docs/10_adr/ADR-008-sqlite-4db-separation.md`; no other file is modified by this procedure.

## Assumptions
- UNK-01 resolved: mdq.sqlite holds documents, chunks, an FTS5 index and `index_state` (file modification times), all derived from Markdown files (Confirmed by repository evidence — `scripts/mcp_servers/mdq/db_schema.py`, `indexer.py`); `scripts/db/recovery.py` and `rotation.py` have no mdq handling.
- User decision (2026-10-08): a `Decision Change` line is added in the form used by ADR-006 and ADR-007 (UNK-02). UNK-04: the restart row also names the ingester, matching the stop-scope row.

## Design decisions
- The new section uses the `###` level that ADR-008 uses under Decision; the structure checker accepts it.
- The Decision Change line and the section text are kept short because the ADR is within about 100 bytes of the 24576-byte size limit enforced by `check_docs_structure.py`.

## Alternatives considered
- Raising the size limit for ADR-008: not needed after trimming the added text.

## Implementation
### Target file
docs/10_adr/ADR-008-sqlite-4db-separation.md

### Procedure
1. Add the Summary sentence and replace the migration Constraint.
2. Fix the stop-scope, restart-condition and rollback-condition rows of the matrix.
3. Add the "Derived Stores Outside the Four Domains" section and the Out of Scope item.
4. Replace Known Deviations and the fifth-domain Review Trigger.
5. Add the Decision Change line and run the documentation checkers.

### Method
Exact-string replacements in one file.

### Details
Code claims keep their evidence labels; no line numbers or counts are added.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_known_deviation_sync.py`, `check_adr_invariant_matrix.py`, `check_adr_structure.py`, `check_adr_reference.py`, `check_docs_consistency.py --domain agent`; `rg` finds none of "RAG process", "No migration mechanism exists", "EVENTBUS-008".

## Completion criteria
- The edits are in place and the checkers pass (REQ-001 to REQ-007).

## Out of scope
- Any file other than `docs/10_adr/ADR-008-sqlite-4db-separation.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-183554 | 20261008-183554 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-183554 | 20261008-183554 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/done/20261008-094453_adr008fix_fix-adr-008-for-mdq.sqlite-and-recovery-matrix.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-183248_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-183554
- **Related target files**: docs/10_adr/ADR-008-sqlite-4db-separation.md