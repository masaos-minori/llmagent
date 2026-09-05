## Goal

Add a citation of the relevant new docs/ remove-categories adjacent to this
file's existing "No source-code line numbers" citation (REQ-005).

## Scope

- In-scope: one citation line/addition in `skills/test-audit/workflow.md`,
  adjacent to the confirmed existing citation.
- Out-of-scope: any other line in this file; any other skill file; `skills/DESIGN.md` itself.

## Assumptions

Only the remove-categories relevant to a test-audit report's own content
(avoiding line-number citations and, by extension, other implementation-detail
listings) are relevant here, not the retain-categories, matching this file's
existing citation context (paired with "Evidence labels", concerning what a
test-audit report should and should not cite).

## Design decisions

Add a short citation matching this file's existing citation style — do not
restate the new categories' definitions.

## Alternatives considered

Restating the remove-category definitions inline — rejected: duplicates
content that must live once in `skills/DESIGN.md`.

## Implementation

### Target file

`skills/test-audit/workflow.md`

### Procedure

1. Confirm the existing citation is still present at the location the Plan
   recorded (line 46: "`skills/DESIGN.md` (Evidence labels, No source-code
   line numbers — needed for...") — re-verified present, unchanged, via
   direct read during this cycle.
2. Extend that citation to also name the relevant new remove-categories,
   once `skills/DESIGN.md` (`implementations/20260905-112342_01`) has landed
   those headings.

### Method

Direct `Edit`: append the new principle heading name(s) to the existing
parenthetical citation list at line 46.

### Details

Single-line addition to an existing "Read, if not already loaded" or
equivalent required-files citation list. No other content in this file
changes.

## Compatibility considerations

No interface change — documentation citation addition to a skill workflow
file. Does not alter this skill's existing audit procedure steps.

## Security considerations

N/A — documentation-only.

## Rollback considerations

Single-line edit under version control; revert via `git revert` if wording
proves wrong. Depends on `_01` landing first (heading-name dependency).

## Validation plan

Manual review: `grep -n "<final heading name(s) from _01>"
skills/test-audit/workflow.md` returns at least one match.

## Completion criteria

The file cites at least one relevant new remove-category by name, adjacent
to its existing "No source-code line numbers" citation.

## Out of scope

Any other file. The retain-categories citation (not relevant to this file).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Depends on `implementations/20260905-112342_01` landing first (heading-name dependency) |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Manual grep review only, per Validation plan |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: this row's target file is itself the documentation being updated |

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
- **Related target files**: skills/test-audit/workflow.md
