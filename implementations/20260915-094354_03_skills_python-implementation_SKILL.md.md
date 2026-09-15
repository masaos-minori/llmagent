## Goal
Define "smallest change" in `skills/python-implementation/SKILL.md` line 37 (REQ-002)
with a concrete criterion.

## Scope
In scope: the "smallest change; preserve unrelated behavior; apply modern Python
features" cell of the Phase 5 (Semantic Safe Modification) table row. Out of scope:
the other 2 clauses in the same cell ("preserve unrelated behavior", "apply modern
Python features" — neither is negative-only or vague in the same way, and neither is
in the Plan's Requirements); `skills/python-implementation/workflow.md`'s own
"sufficient context" wording (a separate target-file row in this same Plan); any other
section of this file.

## Assumptions
- Adding one short clause will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the criterion reuses this same skill's own `workflow.md` Step 5c ("File
editing rules" — "keep diffs small and intentional") rather than inventing a new
standard, since that Step already exists specifically to operationalize file-editing
scope within this same skill.

## Alternatives considered
- Reusing `issue-to-plan`'s ≤3-file Path A threshold here too — rejected: "smallest
  change" in this Phase 5 table row describes a single file's own diff size during
  implementation, not a cross-file Plan-scope count; the two concepts operate at
  different granularities (one file's diff vs. how many files a Plan touches), so
  reusing the Path A number would conflate them.
- A new numeric line-count threshold (e.g. "no more than N changed lines") — rejected:
  the Plan's Constraint prefers reusing an existing standard; `workflow.md` Step 5c
  already exists for this exact purpose.

## Implementation
### Target file
skills/python-implementation/SKILL.md

### Procedure
1. Open the Phase overview table, locate Phase 5's row ("Semantic Safe
   Modification").
2. Append a cross-reference to `workflow.md` Step 5c within the "smallest change"
   cell.
3. Leave the rest of the table and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full Phase 5 table row
(unique in the file), appending the cross-reference within the cell.

### Details
Change the Phase 5 row's third column from:
`smallest change; preserve unrelated behavior; apply modern Python features`
to:
`smallest change (see \`workflow.md\` Step 5c "keep diffs small and intentional");
preserve unrelated behavior; apply modern Python features`

Do not alter the Phase number, Phase name, or the "Goal / AI Action" wording for any
other row in the table.

## Compatibility considerations
This file is referenced by 5+ other repository files (Plan Affected areas). The
change is confined to one table cell and must not break the table's Markdown
structure (column count, pipe alignment). No public/runtime interface or code
behavior is affected (this is a skill instruction file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one table cell; revertable independently
of the other 7 documents in this pass via `git checkout -- skills/python-
implementation/SKILL.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/python-implementation/SKILL.md` — confirm only the Phase 5 row's
  cell changed, table structure intact, no other row touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (the new clause references
  `workflow.md` Step 5c by name).

## Completion criteria
The "smallest change" clause has a concrete cross-referenced criterion; the table's
other cells and rows are unchanged; `tools/check_skills_references.py` passes (Plan
AC-2's python-implementation/SKILL.md half).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document, including `skills/python-implementation/workflow.md`'s own row for the same
Requirement ID); the other 2 clauses in the same table cell; any other row or section
of `skills/python-implementation/SKILL.md`; any other evaluation criterion from the
source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-102047 | 20260915-102047 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-102047 | 20260915-102047 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-102047 | 20260915-102047 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-102047 | 20260915-102047 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-002 (define "smallest change" in python-implementation/SKILL.md)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: skills/python-implementation/SKILL.md