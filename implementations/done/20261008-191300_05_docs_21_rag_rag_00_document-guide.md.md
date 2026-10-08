## Goal
Update the front matter entry and the link. (REQ-002 of the Plan: REQ-002).

## Scope
- Only `docs/21_rag/rag_00_document-guide.md`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): the adr009fix content change is committed first, then the rename (UNK-01). The open plans that cite the old path are not edited (UNK-02).

## Design decisions
- Two exact-string replacements.

## Alternatives considered
- Editing the open plans `plans/20261008-164920_plan.md` and `plans/20261008-165548_plan.md`: rejected; they belong to other sessions.

## Implementation
### Target file
docs/21_rag/rag_00_document-guide.md

### Procedure
1. Replace the old file name in the front matter `related` list and in the link.

### Method
Two exact-string replacements.

### Details
Mechanical change; no ADR body text is altered.

## Compatibility considerations
- Documentation only; links to the old file name stop resolving, which is why every live reference is updated.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- The documentation checkers (quality, structure, content_policy, known_deviation_sync, adr_invariant_matrix, adr_structure, adr_reference, `check_docs_consistency.py --domain rag`) and a repository-wide `rg -n -i ft5` excluding archived work items.

## Completion criteria
- The change is in place and the checkers pass (REQ-002).

## Out of scope
- Any file other than `docs/21_rag/rag_00_document-guide.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-191355 | 20261008-191355 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-191355 | 20261008-191355 |  |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/done/20261008-094456_adr009ren_rename-adr-009-file-from-ft5-to-fts5-and-update-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-190605_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-191300
- **Related target files**: docs/21_rag/rag_00_document-guide.md