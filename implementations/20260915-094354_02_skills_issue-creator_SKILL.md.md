## Goal
Define "small, reviewable issues" in `skills/issue-creator/SKILL.md` line 70 (REQ-001)
with a concrete, issue-scoped criterion distinct from `issue-to-plan`'s file-count
threshold.

## Scope
In scope: the "Prefer small, reviewable issues over broad, vague issues." bullet. Out
of scope: `skills/issue-to-plan/SKILL.md`'s own "small, reviewable increments" wording
(a separate target-file row in this same Plan, with its own implementation procedure
document); any other section of this file.

## Assumptions
- Adding one short clause will not push this file over the 400-line File Split Rule
  trigger in `skills/DESIGN.md`.
- Per UNK-01's resolution (see Design decisions below), an Issue's own Phase 2 Task
  Grouping criteria — not `issue-to-plan`'s ≤3-file Plan threshold — is the correct
  basis for "small, reviewable" here, since an Issue does not yet have a frozen
  `Implementation Target Files` count; that count is only established later, in the
  Plan `issue-to-plan` produces.

## Design decisions
Resolves the Plan's UNK-01 (Non-blocking) for this row specifically: `issue-creator`'s
"small, reviewable issues" and `issue-to-plan`'s "small, reviewable increments"
(companion Row 1 document) do NOT share the same unit of work. `issue-to-plan`'s unit
is a Plan's `Implementation Target Files` row count, already frozen by the time
Incrementalism applies. `issue-creator`'s unit is pre-Plan: an Issue's scope, decided
by this same skill's own Phase 2 ("Task Grouping") criteria (`workflow.md` — group
when tightly coupled/same reviewable change/shared acceptance criteria; split when
unrelated/different owners/independently completable). Forcing `issue-creator` to
reuse the ≤3-file number would be inaccurate, since an Issue can legitimately name
more than 3 "Target Files or Areas" (`templates/issue.md`) while still being one
small, reviewable unit of work (e.g. a single cross-cutting rename). The correct
cross-reference is therefore to this skill's own Phase 2 criteria, not to
`issue-to-plan`'s Path A threshold — per `skills/python-design/SKILL.md` Core Design
Rules (avoid implementation-reference duplication), naming the existing criteria by
reference rather than restating them.

## Alternatives considered
- Sharing `issue-to-plan`'s exact ≤3-file wording verbatim — rejected per Design
  decisions above: the units genuinely differ, and forcing one number onto both would
  misrepresent an Issue's actual scope unit.
- Inventing a new numeric threshold (e.g. "no more than 3 Required Changes bullets")
  — rejected: the Plan's Constraint requires reusing an existing standard where one
  applies; this skill's own Phase 2 Task Grouping criteria already exist and directly
  answer "is this one small, reviewable issue."

## Implementation
### Target file
skills/issue-creator/SKILL.md

### Procedure
1. Open the section containing "Prefer small, reviewable issues over broad, vague
   issues." (line 70).
2. Append a cross-reference to this skill's own Phase 2 ("Task Grouping") criteria.
3. Leave all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full bullet line
(unique in the file), appending the cross-reference at its end.

### Details
Change:
`Prefer small, reviewable issues over broad, vague issues.`
to:
`Prefer small, reviewable issues over broad, vague issues — use \`workflow.md\` Phase
2's Task Grouping criteria (group vs. split) to decide the right size, not a file
count: an Issue naming several tightly coupled files can still be one small,
reviewable issue.`

Do not alter any other bullet in the same section, and do not alter
`skills/issue-to-plan/SKILL.md` (its own row, addressed by a separate document).

## Compatibility considerations
This file is referenced by 11+ other repository files (Plan Affected areas) — the
change must not alter any existing sentence's wording that another file might quote
verbatim, only append new text after the named bullet. No public/runtime interface or
code behavior is affected (this is a skill instruction file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/issue-creator/
SKILL.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/issue-creator/SKILL.md` — confirm only the named bullet's appended
  clause changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced (the new clause references
  `workflow.md` Phase 2 by name — this check catches a broken cross-reference too).

## Completion criteria
The "small, reviewable issues" bullet has a concrete, issue-scoped criterion distinct
from `issue-to-plan`'s file-count threshold, per UNK-01's resolution; the bullet's
original wording is unchanged; `tools/check_skills_references.py` passes (Plan AC-1's
issue-creator half).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document, including `skills/issue-to-plan/SKILL.md`'s own row for the same
Requirement ID); any other section of `skills/issue-creator/SKILL.md`; any other
evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-102005 | 20260915-102005 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-102005 | 20260915-102005 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-102005 | 20260915-102005 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-102005 | 20260915-102005 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 (define "small, reviewable" for issue-creator's own unit of work)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: skills/issue-creator/SKILL.md