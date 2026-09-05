## Goal

Add a citation of both new docs/ category lists adjacent to this file's
existing individual principle citations (REQ-005).

## Scope

- In-scope: citation additions in `skills/python-documentation/workflow.md`,
  adjacent to the confirmed existing citations at lines 235, 251, 254, 256.
- Out-of-scope: any other line in this file; any other skill file; `skills/DESIGN.md` itself.

## Assumptions

Same as `implementations/20260905-112342_05` (sibling file, same skill): both
new category lists are relevant here, since this is the workflow document for
the skill most directly responsible for generating `docs/*.md` content.

## Design decisions

Add short citations matching this file's existing per-line citation style —
do not restate the new categories' definitions. Since this file cites the 4
existing principles at 4 separate locations (not one consolidated bullet like
`SKILL.md`), add the new category citations at the location most relevant to
each (the "Remove or compress implementation-derived details" section,
confirmed at lines 240+, is the most natural home for both new lists since it
is the section already organized as a remove/keep list).

## Alternatives considered

Adding the new citations at all 4 existing citation locations independently
— rejected: would duplicate the same citation 4 times in one file; the
"Remove or compress implementation-derived details" section already
functions as this file's canonical remove/keep list, matching the new
categories' own remove/retain structure most closely.

## Implementation

### Target file

`skills/python-documentation/workflow.md`

### Procedure

1. Confirm the existing citations are still present at the locations the
   Plan recorded (line 235: "duplication, No source-code line numbers, No
   concrete configuration values, No implementation"; line 251: "(see
   `skills/DESIGN.md` No concrete configuration values)"; line 254:
   "source-code line numbers (see `skills/DESIGN.md` No source-code line
   numbers)"; line 256: "(see `skills/DESIGN.md` No implementation counts)")
   — re-verified present, unchanged, via direct read during this cycle.
2. In the "### Remove or compress implementation-derived details" section
   (confirmed present, beginning at the paragraph containing line 240's
   heading), add the five remove-categories to its existing "Normally remove,
   compress, or replace with source references" bullet list, and add a
   cross-reference to the five retain-categories in that section's
   surrounding prose, once `skills/DESIGN.md`
   (`implementations/20260905-112342_01`) has landed those headings.

### Method

Direct `Edit`: extend the existing bullet list in "### Remove or compress
implementation-derived details" with entries for the five remove-categories
(mirroring that list's existing bullet style, e.g. "complete file lists,
complete public method lists..."), and add one sentence citing the
retain-categories heading by name.

### Details

The existing bullet list already contains near-equivalent entries for some
of the five remove-categories (e.g. "import lists, module-level constant
listings" is adjacent in spirit to "class/function/method... index table");
this row adds the categories not already covered in equivalent form,
cross-referencing `skills/DESIGN.md`'s new heading rather than duplicating
the definition. No other content in this file changes.

## Compatibility considerations

No interface change — documentation citation addition to a skill workflow
file. Does not alter this file's existing remove/keep bullet list structure
beyond the addition itself.

## Security considerations

N/A — documentation-only.

## Rollback considerations

Bullet-list edit under version control; revert via `git revert` if wording
proves wrong. Depends on `_01` landing first (heading-name dependency).

## Validation plan

Manual review: `grep -n "<final heading names from _01>"
skills/python-documentation/workflow.md` returns at least one match.

## Completion criteria

The file cites both new category lists by name, at or adjacent to its
existing "Remove or compress implementation-derived details" section.

## Out of scope

Any other file. Rewriting the existing bullet list's already-covered entries.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | Added remove-categories to the existing "Normally remove..." bullet list (citing "Docs content policy — remove"), and added retain-categories to the "Keep:" prose (citing "Docs content policy — retain"), both in "### Remove or compress implementation-derived details". |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `grep -n "Docs content policy" skills/python-documentation/workflow.md` returns matches |
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
- **Related target files**: skills/python-documentation/workflow.md
