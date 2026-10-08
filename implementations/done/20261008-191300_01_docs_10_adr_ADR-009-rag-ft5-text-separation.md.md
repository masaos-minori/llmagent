## Goal
Rename the ADR file with `git mv`; no body change. (REQ-001 of the Plan: REQ-001).

## Scope
- Only `docs/10_adr/ADR-009-rag-ft5-text-separation.md`; no other file is modified by this procedure.

## Assumptions
- User decision (2026-10-08): the adr009fix content change is committed first, then the rename (UNK-01). The open plans that cite the old path are not edited (UNK-02).

## Design decisions
- The adr009fix content change was committed first (commit `b97efd634`, user decision), so the rename commit is a pure rename.

## Alternatives considered
- Editing the open plans `plans/20261008-164920_plan.md` and `plans/20261008-165548_plan.md`: rejected; they belong to other sessions.

## Implementation
### Target file
docs/10_adr/ADR-009-rag-ft5-text-separation.md

### Procedure
1. Run `git mv` from the old name to `ADR-009-rag-fts5-text-separation.md`.
2. Confirm `git diff --cached -M --stat` records a rename with 100% similarity.

### Method
The adr009fix content change was committed first (commit `b97efd634`, user decision), so the rename commit is a pure rename.

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
- The change is in place and the checkers pass (REQ-001).

## Out of scope
- Any file other than `docs/10_adr/ADR-009-rag-ft5-text-separation.md`.

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/done/20261008-094456_adr009ren_rename-adr-009-file-from-ft5-to-fts5-and-update-references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-190605_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-191300
- **Related target files**: docs/10_adr/ADR-009-rag-ft5-text-separation.md