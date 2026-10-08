## Goal
Resolve the ADR-009 rationale versus fail-fast contradiction, add Decision item 12 and INV-11 for RAG-002, and fix the checklist (REQ-001 to REQ-006 of the Plan).

## Scope
- Only `docs/10_adr/ADR-009-rag-ft5-text-separation.md`; no other file is modified by this procedure. The file keeps its `ft5` name (adr009ren is separate).

## Assumptions
- UNK-01 resolved: `scripts/rag/ingestion/chunk_japanese.py` still appends a sentence only when its normalized text is non-empty, so a sentence with empty normalized text is dropped with its original text (RAG-002 is still accurate).
- User decision (2026-10-08): a `Decision Change` line is added (UNK-03).

## Design decisions
- INV-11 is written as the intended behavior; RAG-002 is the recorded gap until the code fix of `plans/20261008-164920_plan.md` lands.
- INV-11 is listed among the invariants without an automated test, as for INV-05.

## Alternatives considered
- Renaming the file in the same change: rejected; the issue requires separate commits.

## Implementation
### Target file
docs/10_adr/ADR-009-rag-ft5-text-separation.md

### Procedure
1. Rewrite Rationale 3 and the Positive Consequence.
2. Add Decision Details #12 and INV-11, and update the RAG-002 Known Deviation.
3. Fix the Completion Checklist and the Manual Review line.
4. Add the Decision Change line and run the documentation checkers.

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
- The documentation checkers (quality, structure, content_policy, known_deviation_sync, adr_invariant_matrix, adr_structure, adr_reference, `check_docs_consistency.py --domain rag`); `rg` finds neither "Data loss on normalization failure is prevented" nor "not yet registered".

## Completion criteria
- The edits are in place and the checkers pass (REQ-001 to REQ-006).

## Out of scope
- Any file other than `docs/10_adr/ADR-009-rag-ft5-text-separation.md`, including the ledger and `adr-index.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-185334 | 20261008-185334 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-185334 | 20261008-185334 |  |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006
- **Source issue**: issues/done/20261008-094455_adr009fix_resolve-adr-009-normalization-contradiction-and-inv-11.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-185107_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-185334
- **Related target files**: docs/10_adr/ADR-009-rag-ft5-text-separation.md