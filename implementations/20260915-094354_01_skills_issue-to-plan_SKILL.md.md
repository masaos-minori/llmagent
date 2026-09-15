## Goal
Define "small, reviewable increments" in `skills/issue-to-plan/SKILL.md` line 106
(REQ-001) with a concrete threshold, reusing this same skill's own Path A ≤3-file
rule.

## Scope
In scope: the "**Incrementalism**: Design the implementation steps in small,
reviewable increments." bullet under `## Core Execution Rules`. Out of scope: any
other bullet in that section; `skills/issue-creator/SKILL.md`'s own "small, reviewable
issues" wording (a separate target-file row in this same Plan, with its own
implementation procedure document); any other section of this file.

## Assumptions
- Adding one short cross-reference clause will not push this file over the 400-line
  File Split Rule trigger in `skills/DESIGN.md`.
- Per UNK-01's resolution (see Design decisions below), this skill's own Path A
  ≤3-file threshold is the correct unit for "small, reviewable increments" here, since
  Incrementalism in this skill governs a Plan's `Implementation steps`, which map
  directly to `Implementation Target Files` rows — the same unit Path A already
  counts.

## Design decisions
Resolves the Plan's UNK-01 (Non-blocking) for this row specifically: this skill's
"small, reviewable increments" describes Plan `Implementation steps`, each tied to a
specific `Implementation Target Files` row (`templates/plan.md`) — the identical unit
Path A's ≤3-file threshold already counts (`SKILL.md` Routing, `[Path A] Small Task`).
Cross-referencing that existing threshold is therefore a direct, same-unit reuse, not
an approximation — unlike `issue-creator`'s "small, reviewable issues" (a separate
document, see the companion Row 2 document for that file's own resolution), which
concerns Issue scope rather than a Plan's file count. This confirms the Plan's
Design section's framing (`skills/python-design/SKILL.md` Core Design Rules: avoid
implementation-reference duplication — reference the existing rule instead of
restating it).

## Alternatives considered
- Stating a new standalone increment-size definition specific to Incrementalism
  (e.g. "no more than 3 files per step") — rejected: this would duplicate Path A's
  ≤3-file rule under new wording, risking future drift between the two if either is
  edited independently; a cross-reference avoids that.

## Implementation
### Target file
skills/issue-to-plan/SKILL.md

### Procedure
1. Open `## Core Execution Rules`, locate the "**Incrementalism**" bullet (line 106).
2. Append a cross-reference to this same skill's Path A ≤3-file threshold.
3. Leave the rest of `## Core Execution Rules` and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full "Incrementalism"
bullet line (unique in the file), appending the cross-reference at its end.

### Details
Change:
`- **Incrementalism**: Design the implementation steps in small, reviewable
increments. Each step MUST leave the codebase in a testable state.`
to:
`- **Incrementalism**: Design the implementation steps in small, reviewable
increments — reuse this skill's own Path A ≤3-file threshold (see Routing above) as
the concrete size bound per step, where applicable. Each step MUST leave the codebase
in a testable state.`

Do not alter the "Each step MUST leave the codebase in a testable state." sentence, or
any other bullet in `## Core Execution Rules`.

## Compatibility considerations
This file is referenced by 42+ other repository files (Plan Affected areas) — the
change must not alter any existing sentence's wording that another file might quote
verbatim, only insert new text mid-bullet. No public/runtime interface or code
behavior is affected (this is a skill instruction file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/issue-to-plan/
SKILL.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/issue-to-plan/SKILL.md` — confirm only the Incrementalism bullet's
  inserted clause changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The "small, reviewable increments" bullet has a concrete cross-referenced threshold;
the bullet's original wording and the rest of the section are unchanged;
`tools/check_skills_references.py` passes (Plan AC-1's issue-to-plan half).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document, including `skills/issue-creator/SKILL.md`'s own row for the same
Requirement ID); any other section of `skills/issue-to-plan/SKILL.md`; any other
evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-101917 | 20260915-101917 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-101917 | 20260915-101917 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-101917 | 20260915-101917 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-101917 | 20260915-101917 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-001 (define "small, reviewable" for issue-to-plan's own unit of work)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: skills/issue-to-plan/SKILL.md