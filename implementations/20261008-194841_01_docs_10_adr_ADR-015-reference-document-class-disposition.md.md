## Goal
Make ADR-015's scope decidable from document content, remove the stale domain lists and the historical reference, and record the decision change (REQ-001 to REQ-007 of the Plan).

## Scope
- Only `docs/10_adr/ADR-015-reference-document-class-disposition.md`; no other file is modified by this procedure.

## Assumptions
- UNK-03 resolved: no other document uses the old scope wording; only `governance_02_documentation-metadata.md` mentions `class: Reference` as a field.
- User decision (2026-10-08): a `Decision Change` line is added as a task-level approval; the Named Approval Record (repository owner, 2026-09-19) is left unchanged (UNK-01). The new checklist item is added unchecked (UNK-02).

## Design decisions
- The new Scope applies to every document with a generated guarded block; `class: Reference` is a recommendation.
- No domain names or counts are added; the sections refer to `DOMAIN_GENERATORS` and the Implementation Notes.

## Alternatives considered
- Writing a new named approval on the owner's behalf: rejected; only the task-level line is added.

## Implementation
### Target file
docs/10_adr/ADR-015-reference-document-class-disposition.md

### Procedure
1. Replace the Context sentence and the first Assumption.
2. Replace the Scope.
3. Remove "the source issue" from Alternative C and "three domains" from Rationale 3.
4. Add the unchecked Completion Checklist item.
5. Add the `Decision Change` line to the Approval Record and run the documentation checkers.

### Method
Exact-string replacements in one file.

### Details
Code claims keep their evidence labels; no counts are added.

## Compatibility considerations
- Documentation only.

## Security considerations
- None.

## Rollback considerations
- Revert the commit.

## Validation plan
- The documentation checkers (quality, structure, content_policy, known_deviation_sync, adr_invariant_matrix, adr_structure, adr_reference, `check_docs_consistency.py --domain agent`); `rg` finds none of "source issue", "three domains", "MCP/RAG/deployment".

## Completion criteria
- The edits are in place and the checkers pass (REQ-001 to REQ-007).

## Out of scope
- Any file other than `docs/10_adr/ADR-015-reference-document-class-disposition.md`; adding `class` fields to other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the change in Implementation > Procedure | Completed | 20261008-194841 | 20261008-194841 |  |
| 2 | Run the validation in the Validation plan | Completed | 20261008-194841 | 20261008-194841 |  |

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
- **Source issue**: issues/done/20261008-094501_adr015fix_fix-adr-015-scope-and-generator-domain-description.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-194514_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261008-194841
- **Related target files**: docs/10_adr/ADR-015-reference-document-class-disposition.md