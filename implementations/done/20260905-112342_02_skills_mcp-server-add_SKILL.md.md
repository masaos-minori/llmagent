## Goal

Add a citation of the new "literal port numbers" docs/ remove-category
adjacent to this file's existing "No concrete configuration values" citation
(REQ-005).

## Scope

- In-scope: one citation line/addition in `skills/mcp-server-add/SKILL.md`,
  adjacent to the confirmed existing citation.
- Out-of-scope: any other line in this file; any other skill file (covered by
  sibling documents `_03` through `_10`); `skills/DESIGN.md` itself (covered
  by `_01`).

## Assumptions

Only the "literal port numbers" remove-category is relevant here — not the
retain-categories or the other four remove-categories — since this file's
existing citation concerns configuration values (of which port numbers are
one instance) specifically, not general documentation structure (per Plan
Assumptions).

## Design decisions

Add a short citation matching this file's existing one-line citation style —
do not restate the new category's definition (which lives once in
`skills/DESIGN.md`, per that document's own "Avoid implementation-reference
duplication" discipline applied reflexively here).

## Alternatives considered

Restating the "literal port numbers" definition inline — rejected: duplicates
content that must live once in `skills/DESIGN.md` (per this Plan's own Design
section).

## Implementation

### Target file

`skills/mcp-server-add/SKILL.md`

### Procedure

1. Confirm the existing citation is still present at the location the Plan
   recorded (line 22, within the sentence "New servers must use the next free
   port above every port currently assigned — derive it at task time (see
   Prerequisites), per `skills/DESIGN.md` No concrete configuration values.")
   — re-verified present, unchanged, via direct read during this cycle.
2. Extend that same sentence (or add an adjacent clause) to also cite the new
   "literal port numbers" remove-category by name, once `skills/DESIGN.md`
   (this Plan's row `_01`) has landed that heading.

### Method

Direct `Edit`: append the new principle's heading name to the existing
citation clause, e.g. "...per `skills/DESIGN.md` No concrete configuration
values (and, for documentation, the literal port numbers remove-category)."
— exact wording deferred to whatever heading text `_01` lands, since this row
executes after `_01` in `seq` order.

### Details

This is a single-sentence addition, not a new paragraph — the file's existing
style states each principle citation inline within the sentence it qualifies,
not as a separate bullet. No other content in this file changes.

## Compatibility considerations

No interface change — this is a documentation citation addition to a skill
instruction file, not code. Does not alter this skill's existing
Prerequisites, Port/role table reference, or module-path pattern guidance.

## Security considerations

N/A — documentation-only, no code, credentials, or access-control content
affected.

## Rollback considerations

Single-sentence edit under version control; revert via `git revert` if the
wording proves wrong. Depends on `_01`'s heading-name choice landing first
(same Plan, `seq` 01 precedes 02) — if `_01` is not yet implemented when this
row is executed, this row cannot cite the heading by its final name; treat
this as this row's own blocking dependency, not a new target-file discovery.

## Validation plan

Manual review: `grep -n "literal port numbers\|<final heading name from _01>"
skills/mcp-server-add/SKILL.md` returns at least one match (per Plan
Validation plan's second row).

## Completion criteria

The file cites the new "literal port numbers" remove-category by name,
adjacent to its existing "No concrete configuration values" citation.

## Out of scope

Any other file. The retain-categories citation (not relevant to this file,
per Assumptions).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260905 | 20260905 | Added sentence citing "Docs content policy — remove" (landed heading from `implementations/done/20260905-112342_01`) adjacent to the existing "No concrete configuration values" citation at line 22. |
| 2 | Add or update tests per Validation plan | Completed | 20260905 | 20260905 | N/A: documentation-only, no test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260905 | 20260905 | `grep -n "Docs content policy" skills/mcp-server-add/SKILL.md` returns a match |
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
- **Related target files**: skills/mcp-server-add/SKILL.md
