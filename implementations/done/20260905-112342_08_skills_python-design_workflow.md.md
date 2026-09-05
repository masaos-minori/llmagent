## Goal

Add a citation of the new "full file tree" docs/ remove-category adjacent to
this file's existing citation that already names "file trees" as an example
(REQ-005).

## Scope

- In-scope: one citation addition in `skills/python-design/workflow.md`,
  adjacent to the confirmed existing citation at line 182.
- Out-of-scope: any other line in this file; any other skill file; `skills/DESIGN.md` itself.

## Assumptions

Only the "full file tree" remove-category (and, secondarily, any other
remove-category relevant to "generated or mechanically discoverable
details") is relevant here — this is the file whose existing text already
names "file trees" as an example under "Avoid implementation-reference
duplication" (confirmed at line 182: "Apply `skills/DESIGN.md` Avoid
implementation-reference duplication to generated or mechanically
discoverable details (CLI help, configuration schemas, DTO fields, file
trees).") — this is direct evidence that the new category is not a novel
concept but one this file already informally recognized, per Plan
Background.

## Design decisions

Add a short citation matching this file's existing sentence style — do not
restate the new category's definition, and note (in the citation itself)
that "file trees" as already named here is now covered specifically by the
new remove-category.

## Alternatives considered

Rewriting the existing "(CLI help, configuration schemas, DTO fields, file
trees)" parenthetical to remove "file trees" now that it has its own named
category elsewhere — rejected: the parenthetical still correctly illustrates
this principle's own broader scope (design output should not restate
generated/mechanical detail); removing "file trees" from it would narrow this
principle's own illustration rather than simply adding a cross-reference.

## Implementation

### Target file

`skills/python-design/workflow.md`

### Procedure

1. Confirm the existing citations are still present at the locations the
   Plan recorded (line 64: "Apply `skills/DESIGN.md` Avoid
   implementation-reference duplication — list a file, function, or method
   only when the boundary itself is a design decision."; line 182: "Apply
   `skills/DESIGN.md` Avoid implementation-reference duplication to
   generated or mechanically discoverable details (CLI help, configuration
   schemas, DTO fields, file trees).") — re-verified present, unchanged, via
   direct read during this cycle.
2. Immediately after line 182's sentence, add a clause or short sentence
   citing the new "full file tree" remove-category by name, once
   `skills/DESIGN.md` (`implementations/20260905-112342_01`) has landed that
   heading.

### Method

Direct `Edit`: append a clause to the existing sentence at line 182, e.g.
"...(CLI help, configuration schemas, DTO fields, file trees — see also
`skills/DESIGN.md` {full-file-tree heading name})." — exact wording deferred
to whatever heading text `_01` lands.

### Details

Single-clause addition to an existing sentence; the parenthetical's other
three examples (CLI help, configuration schemas, DTO fields) are unchanged.
No other content in this file changes.

## Compatibility considerations

No interface change — documentation citation addition to a skill workflow
file. Does not alter this file's existing package-layout/interface-contract
design guidance.

## Security considerations

N/A — documentation-only.

## Rollback considerations

Single-clause edit under version control; revert via `git revert` if wording
proves wrong. Depends on `_01` landing first (heading-name dependency).

## Validation plan

Manual review: `grep -n "<final heading name from _01>"
skills/python-design/workflow.md` returns at least one match, and the
existing "file trees" parenthetical at line 182 is confirmed still present
alongside it.

## Completion criteria

The file cites the "full file tree" remove-category by name, immediately
adjacent to its existing "file trees" example.

## Out of scope

Any other file. Removing "file trees" from the existing parenthetical (see
Alternatives considered). The retain-categories citation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | Appended a clause to the existing sentence at line 182, citing "Docs content policy — remove" alongside the pre-existing "file trees" example. |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `grep -n "Docs content policy" skills/python-design/workflow.md` returns a match; "file trees" parenthetical confirmed still present |
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
- **Related target files**: skills/python-design/workflow.md
