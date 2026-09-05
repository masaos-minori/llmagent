## Goal

Add a citation of the relevant new docs/ remove-categories adjacent to this
file's existing "Avoid implementation-reference duplication" citation
(REQ-005).

## Scope

- In-scope: one citation line/addition in `skills/issue-creator/workflow.md`,
  adjacent to the confirmed existing citation.
- Out-of-scope: any other line in this file; any other skill file; `skills/DESIGN.md` itself.

## Assumptions

Same as `implementations/20260905-112342_03` (sibling file, same skill): only
the remove-categories relevant to issue authoring are cited here, not the
retain-categories.

## Design decisions

Add a short citation matching this file's existing citation style — do not
restate the new categories' definitions.

## Alternatives considered

Restating the remove-category definitions inline — rejected: duplicates
content that must live once in `skills/DESIGN.md`.

## Implementation

### Target file

`skills/issue-creator/workflow.md`

### Procedure

1. Confirm the existing citation is still present at the location the Plan
   recorded (line 100: "Apply `skills/DESIGN.md` Avoid implementation-reference
   duplication to what implementers are asked to add.") — re-verified
   present, unchanged, via direct read during this cycle.
2. Extend that sentence (or add an adjacent sentence) to also cite the
   relevant new remove-categories by name, once `skills/DESIGN.md`
   (`implementations/20260905-112342_01`) has landed those headings.

### Method

Direct `Edit`: append the new principle heading name(s) to the existing
citation sentence — exact wording deferred to whatever heading text `_01`
lands.

### Details

Single-sentence addition within the existing "For documentation-related
issues, focus on..." paragraph. No other content in this file changes.

## Compatibility considerations

No interface change — documentation citation addition to a skill workflow
file.

## Security considerations

N/A — documentation-only.

## Rollback considerations

Single-sentence edit under version control; revert via `git revert` if
wording proves wrong. Depends on `_01` landing first (heading-name
dependency).

## Validation plan

Manual review: `grep -n "<final heading name(s) from _01>"
skills/issue-creator/workflow.md` returns at least one match.

## Completion criteria

The file cites at least one relevant new remove-category by name, adjacent
to its existing "Avoid implementation-reference duplication" citation.

## Out of scope

Any other file. The retain-categories citation (not relevant to this file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | Extended the existing sentence at line 100 to also cite "Docs content policy — remove". |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `grep -n "Docs content policy" skills/issue-creator/workflow.md` returns a match |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260905 | 20260905 | N/A: this row's target file is itself the documentation being updated |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/done/20260903-200135_docscope1_define-design-intent-content-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-101850_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260905-112342
- **Related target files**: skills/issue-creator/workflow.md
