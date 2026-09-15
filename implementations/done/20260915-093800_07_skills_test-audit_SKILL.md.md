## Goal
Add one positive-form alternative clause to `skills/test-audit/SKILL.md`'s "MUST NOT
assume test coverage from file names alone" item (REQ-007), so the prohibition
resolves to a concrete next action.

## Scope
In scope: the "MUST NOT assume test coverage from file names alone." bullet under
`## Core Execution Rules`. Out of scope: the adjacent "MUST NOT stop at high-level
commentary" bullet and the "Production code: see Phase Boundaries above" bullet; any
other section of this file; any other file (see the Plan's other 7 target-file rows).

## Assumptions
- Adding one short alternative clause will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the alternative clause names the concrete verification action (open and
read the test file's actual content/assertions) rather than a vague instruction,
consistent with this skill's own emphasis (the adjacent bullet) on not stopping at
high-level commentary.

## Alternatives considered
- Cross-referencing a specific `safety.md`/`evidence.md` section for the verification
  procedure — considered, but the source Issue's Required Changes and this Plan's
  REQ-007 specify only the clause text itself with no named cross-reference target;
  a direct, self-contained alternative was used instead to avoid inventing a
  cross-reference the Plan did not specify.

## Implementation
### Target file
skills/test-audit/SKILL.md

### Procedure
1. Open `## Core Execution Rules`, locate "MUST NOT assume test coverage from file
   names alone."
2. Append an alternative clause to that bullet.
3. Leave the other bullets in this section and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full bullet line
(unique in the file), appending the alternative clause at its end.

### Details
Change:
`MUST NOT assume test coverage from file names alone.`
to:
`MUST NOT assume test coverage from file names alone — instead, open the matching test
file and confirm it actually exercises the behavior in question before crediting it as
coverage.`

Do not alter the adjacent "Production code: see Phase Boundaries above." bullet or the
"MUST NOT stop at high-level commentary" bullet.

## Compatibility considerations
N/A: additive prose-only change to a skill instruction file; no public/runtime
interface, no code behavior affected.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/test-audit/SKILL.md`
(pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/test-audit/SKILL.md` — confirm only the appended clause changed,
  no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The "MUST NOT assume test coverage from file names alone" bullet has an adjacent
positive-form alternative; its original wording and the adjacent bullets are
unchanged; `tools/check_skills_references.py` passes (Plan AC-7, AC-8 for this file's
portion).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the adjacent bullets in `## Core Execution Rules`; any other section of
`skills/test-audit/SKILL.md`; any other evaluation criterion from the source review
batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-101259 | 20260915-101259 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-101259 | 20260915-101259 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-101259 | 20260915-101259 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-101259 | 20260915-101259 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-007 (add positive alternative to "MUST NOT assume test coverage from file names alone")
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: skills/test-audit/SKILL.md