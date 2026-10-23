## Goal

Add a `Core Testing Rules` line to `skills/python-test-and-fix/SKILL.md` stating that a
test built from a stub whose `await` behaviour differs from the production method is the
same defect class as an assertion that cannot fail (REQ-011).

## Scope

Skill-doc edit to `skills/python-test-and-fix/SKILL.md` only. Adds one bullet to the
"Core Testing Rules (Strictly Enforced for AI)" section (`:18-23`). This row is
**conditional**: only if REQ-011's rule is not already carried by a line a prior task
(`repl003`) added. Verified at HEAD the rule is **not** present (search for "cannot
fail" / "await behavior" / "stub" mismatch in `skills/python-test-and-fix/` returns no
match), so this row applies.

## Assumptions

- The existing `Core Testing Rules` bullets cover blind-expectation changes, flaky-fix
  anti-patterns, mock cleanliness, and tool-hallucination — none covers a stub whose
  `await` behaviour the production method lacks.
- A stub whose `await` yields (or raises directly) while the real method blocks is the
  mechanism behind the pre-existing false coverage in `tests/agent/test_repl.py` and the
  coordinator tests (plan Background, REQ-011).

## Design decisions

- Add one bullet under `Core Testing Rules`: a test that asserts a branch fired must be
  built from the production step body, not from a stub whose `await` behaviour the
  production code does not have; such a stub is the same defect class as an assertion
  that cannot fail.
- Place it among the strict rules so it is enforced like the others, not deferred to
  `workflow.md`.
- Confirm `check_skills_references.py` still passes after the edit (`routing.md` skill
  checks).

## Alternatives considered

- Recording the rule in `docs/` instead — rejected: this is a testing-contract rule, and
  the plan states `docs/` is not its home; the skill's `Core Testing Rules` is.
- Deferring to `workflow.md` — rejected: the rule is strictly enforced policy, matching
  the other bullets.

## Implementation

### Target file

`skills/python-test-and-fix/SKILL.md`

### Procedure

1. Confirm the rule is absent (re-run the search above; if it is now present because a
   later task added it, **do not** edit — the expected outcome is no second edit).
2. Add one bullet to the `Core Testing Rules (Strictly Enforced for AI)` section:
   > - **Build Timeout / Branch Tests off the Production Body**: A test that asserts a
     branch fired (e.g. a timeout, a fallback) MUST exercise the real production step
     body, not a stub whose `await` behaviour the production method lacks. A stub whose
     await differs from production is the same defect class as an assertion that cannot
     fail.
3. Run `check_skills_references.py` and the skill's referenced tooling.

### Details

- Keep the bullet parallel in tone to the existing three (imperative, bold lead-in).
- Do not touch the Task Routing / Phase overview sections — out of scope.

## Compatibility considerations

- Purely additive bullet; no existing rule changed.

## Security considerations

- N/A: documentation/skill edit.

## Rollback considerations

- Remove the added bullet. Single logical commit; reversible.

## Validation plan

- `uv run python tools/check_skills_references.py` (passes; `routing.md` skill checks).
- Manual: confirm the new bullet reads as a strict rule alongside the others.

## Completion criteria

The `Core Testing Rules` section carries the REQ-011 rule (build branch/timeout tests
off the production body), `check_skills_references.py` passes, and no duplicate bullet
exists.

## Out of Scope

- All production/test/doc edits — rows 1-7.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add REQ-011 bullet to Core Testing Rules | Pending | — | — | Conditional; rule absent at HEAD |
| 2 | Run skill checks (`routing.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Rule may have been added by a later task; re-verify before editing | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-011
- **Source issue**: `issues/20261021-093421_shutdown001-wal-checkpoint-timeout-guard-cannot-fire.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-043330_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-084708
- **Related target files**: `skills/python-test-and-fix/SKILL.md`
