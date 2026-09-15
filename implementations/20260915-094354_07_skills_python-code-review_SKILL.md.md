## Goal
Link "conventions" in `skills/python-code-review/SKILL.md` line 68 (REQ-005)
explicitly to `rules/coding.md`.

## Scope
In scope: the "Respect project conventions and explain trade-offs." bullet. Out of
scope: any other bullet in the same section; any other section of this file.

## Assumptions
- Adding one short cross-reference clause will not push this file over the 400-line
  File Split Rule trigger in `skills/DESIGN.md`.
- `rules/coding.md` (confirmed via Reference Files below) is the correct, single
  target for "conventions" — it is this project's canonical shared coding-conventions
  file, referenced as such by `routing.md`'s "Always load alongside the skill" table.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), this is a pure cross-reference — no new threshold is invented, since
`rules/coding.md` already defines the conventions in question, per the Plan's own
Design section ("REQ-005 is a pure cross-reference (no new threshold needed...)").

## Alternatives considered
- Listing a few example conventions inline (e.g. "line length, import order") instead
  of a bare cross-reference — rejected: this would duplicate `rules/coding.md`'s
  content and risk drifting out of sync with it; a name-only reference is the
  intended, minimal fix per the Plan's Required Changes.

## Implementation
### Target file
skills/python-code-review/SKILL.md

### Procedure
1. Locate "Respect project conventions and explain trade-offs." (line 68).
2. Append an explicit cross-reference to `rules/coding.md`.
3. Leave the rest of the surrounding section unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full bullet line
(unique in the file), appending the cross-reference at its end.

### Details
Change:
`- Respect project conventions and explain trade-offs.`
to:
`- Respect project conventions (see \`rules/coding.md\` for the canonical list) and
explain trade-offs.`

Do not alter any other bullet in the same section or any other part of the file.

## Compatibility considerations
This file is referenced by 7+ other repository files (Plan Affected areas). No
public/runtime interface or code behavior is affected (this is a skill instruction
file).

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/python-code-review/
SKILL.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/python-code-review/SKILL.md` — confirm only the named bullet's
  appended clause changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm the new `rules/
  coding.md` cross-reference resolves to an existing file (this check specifically
  validates backtick-quoted `rules/`/`skills/`/`templates/` references).

## Completion criteria
The "conventions" bullet explicitly links to `rules/coding.md`; the bullet's original
wording is unchanged; `tools/check_skills_references.py` passes (Plan AC-5).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); any other section of `skills/python-code-review/SKILL.md`; any other
evaluation criterion from the source review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-102358 | 20260915-102358 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-102358 | 20260915-102358 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-102358 | 20260915-102358 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-102358 | 20260915-102358 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-005 (link "conventions" to rules/coding.md)
- **Source issue**: issues/20260914-114854_skillqa02_replace-vague-qualifiers-with-concrete-criteria.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-085149_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-094354
- **Related target files**: skills/python-code-review/SKILL.md