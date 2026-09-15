## Goal
Add one positive-form alternative clause to `skills/test-audit/workflow.md`'s "Do not
silently ignore skipped or blocked tests" item (REQ-008), so the prohibition resolves
to a concrete next action.

## Scope
In scope: the "Do not silently ignore skipped or blocked tests." bullet under
`## Important Rules`. Out of scope: the other 2 bullets in the same section ("If CI
and local commands differ, report that explicitly." and "Prefer repository-defined
commands over invented ones..."); any other section of this file; any other file (see
the Plan's other 7 target-file rows).

## Assumptions
- Adding one short alternative clause will not push this file over the 400-line File
  Split Rule trigger in `skills/DESIGN.md`.

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("Avoid implementation-reference
duplication"), the alternative clause names the concrete reporting action (record the
skipped/blocked test explicitly in the audit findings, per this skill's own evidence
classification) rather than a vague instruction.

## Alternatives considered
- Cross-referencing `evidence.md`'s classification procedures directly (this section's
  own lead-in already says "in addition to `evidence.md`'s classification
  procedures") — considered and adopted in the final wording below, since it reuses
  an already-named file in this same section rather than inventing a new reference.

## Implementation
### Target file
skills/test-audit/workflow.md

### Procedure
1. Open `## Important Rules`, locate "Do not silently ignore skipped or blocked
   tests."
2. Append an alternative clause to that bullet.
3. Leave the other 2 bullets in this section and all surrounding content unchanged.

### Method
Use `Edit` with an `old_string`/`new_string` pair covering the full bullet line
(unique in the file), appending the alternative clause at its end.

### Details
Change:
`Do not silently ignore skipped or blocked tests.`
to:
`Do not silently ignore skipped or blocked tests — instead, record each one explicitly
in the audit findings using \`evidence.md\`'s classification procedures, with the
reason it was skipped or blocked.`

Do not alter the other 2 bullets in `## Important Rules` or the section's lead-in
sentence.

## Compatibility considerations
N/A: additive prose-only change to a skill instruction file; no public/runtime
interface, no code behavior affected.

## Security considerations
N/A: no secrets, credentials, or executable content involved — plain Markdown prose
addition only.

## Rollback considerations
Single-file, additive-only edit confined to one bullet; revertable independently of
the other 7 documents in this pass via `git checkout -- skills/test-audit/
workflow.md` (pre-commit) or a follow-up commit reverting this file only.

## Validation plan
- `git diff skills/test-audit/workflow.md` — confirm only the appended clause
  changed, no other line touched.
- `uv run python tools/check_skills_references.py` — confirm no broken
  `rules/`/`skills/`/`templates/` reference was introduced.

## Completion criteria
The "Do not silently ignore skipped or blocked tests" bullet has an adjacent
positive-form alternative; its original wording and the other 2 bullets in
`## Important Rules` are unchanged; `tools/check_skills_references.py` passes (Plan
AC-8 for this file's portion, the final of the 8 target files in this Plan).

## Out of scope
The other 7 target files in this Plan (each has its own implementation procedure
document); the other 2 bullets in `## Important Rules`; any other section of
`skills/test-audit/workflow.md`; any other evaluation criterion from the source
review batch.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260915-101342 | 20260915-101342 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260915-101342 | 20260915-101342 | N/A: no automated test for this file type — see Validation plan |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260915-101342 | 20260915-101342 | Only `tools/check_skills_references.py` applies (Markdown, not `scripts/`) |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260915-101342 | 20260915-101342 | N/A: no `docs/*.md` update required |

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
- **Requirement ID**: REQ-008 (add positive alternative to "Do not silently ignore skipped or blocked tests")
- **Source issue**: issues/20260914-114822_skillqa01_negative-instructions-add-positive-alternatives.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260915-084829_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-093800
- **Related target files**: skills/test-audit/workflow.md