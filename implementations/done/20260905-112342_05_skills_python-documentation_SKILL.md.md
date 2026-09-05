## Goal

Add a citation of both new docs/ category lists (remove-categories,
retain-categories) adjacent to this file's existing 4-principle citation
(REQ-005).

## Scope

- In-scope: one citation addition in `skills/python-documentation/SKILL.md`,
  adjacent to the confirmed existing 4-principle citation.
- Out-of-scope: any other line in this file; any other skill file; `skills/DESIGN.md` itself.

## Assumptions

Unlike most of this Plan's other 8 skill-file rows, both new category lists
are relevant here (not only the remove-categories) — this is the skill most
directly responsible for generating `docs/*.md` content, so the
retain-categories (what design-intent content to include) are as relevant as
the remove-categories (what implementation detail to exclude), per Plan
Background.

## Design decisions

Add a short citation matching this file's existing bullet-per-principle
style — do not restate the new categories' definitions.

## Alternatives considered

Citing only the remove-categories, mirroring the other 8 skill-file rows —
rejected: this skill actively generates `docs/*.md` content, so omitting the
retain-categories here would leave its most relevant guidance (what to write
instead of implementation detail) uncited.

## Implementation

### Target file

`skills/python-documentation/SKILL.md`

### Procedure

1. Confirm the existing citation is still present at the location the Plan
   recorded (lines 62-63: "**Remove or compress implementation-derived
   details**: see `skills/DESIGN.md` Avoid implementation-reference
   duplication." and "**No line numbers, no config values, no counts**: see
   `skills/DESIGN.md` No source-code line numbers, No concrete configuration
   values, No implementation counts.") — re-verified present, unchanged, via
   direct read during this cycle.
2. Add a new bullet immediately after those two, citing both new category
   lists by name, once `skills/DESIGN.md`
   (`implementations/20260905-112342_01`) has landed those headings.

### Method

Direct `Edit`: insert one new bullet in the existing "Core rules" (or
equivalent) bullet list, matching the file's existing
"**Bold-label**: see `skills/DESIGN.md` {heading}." format — exact heading
names deferred to whatever text `_01` lands.

### Details

New bullet example shape (final wording depends on `_01`'s landed heading
names): "**Docs content policy**: see `skills/DESIGN.md` {remove-categories
heading}, {retain-categories heading}." No other bullet in this list is
modified.

## Compatibility considerations

No interface change — documentation citation addition to a skill instruction
file. Does not alter this skill's existing evidence-label, minimal-diff, or
boundary-respect rules.

## Security considerations

N/A — documentation-only.

## Rollback considerations

Single-bullet edit under version control; revert via `git revert` if wording
proves wrong. Depends on `_01` landing first (heading-name dependency).

## Validation plan

Manual review: `grep -n "<final heading names from _01>"
skills/python-documentation/SKILL.md` returns at least one match.

## Completion criteria

The file cites both new category lists by name, adjacent to its existing
4-principle citation.

## Out of scope

Any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | Added a new bullet immediately after the existing 4-principle citation (lines 62-63), citing both "Docs content policy — remove" and "Docs content policy — retain". |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `grep -n "Docs content policy" skills/python-documentation/SKILL.md` returns matches |
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
- **Related target files**: skills/python-documentation/SKILL.md
