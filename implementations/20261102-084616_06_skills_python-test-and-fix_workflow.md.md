## Goal

State in one sentence that a test session which changes production database files fails (`REQ-006`: guarantee in the test guidance).

## Scope

- One sentence in the production-isolation paragraph of `skills/python-test-and-fix/workflow.md` (Step 2, "Inspect Before Changing").

## Assumptions

- Plan overlaps: none names this Plan (`tools/check_plan_target_overlaps.py`, 2026-11-02); no sibling Plan targets this file: compatible.
- Verified 2026-11-02: the paragraph beginning "Before the first test run, apply `SKILL.md` Core rule" says the guard fails a test that opens a database or `FileHandler` under `/opt/llm`, and does not mention a changed production file; `skills/python-test-and-fix/SKILL.md` Core rule "Verify Production Isolation Before Running Tests" is consistent and stays unchanged.
- This is a `skills/*.md` procedure edit, not documentation of code behavior routed through `python-documentation` (`routing.md` Documentation row exception); no `docs/*.md` change.

## Design decisions

- Add the sentence directly after the guard-coverage sentence, as part of the same paragraph, with no new heading and no new cross-file reference.

## Alternatives considered

- N/A: the Plan considered `rules/toolchain.md` and kept this location.

## Implementation
### Target file
`skills/python-test-and-fix/workflow.md`

### Procedure
1. After the clause listing what the guard does not cover ("ports or other kinds of write"), add: "A session that changes, adds, or removes any file under `/opt/llm/db` (including through a subprocess the per-test guard cannot see) fails at finish, naming each file."

### Method
- Edit the paragraph in place; keep the line wrap used by the surrounding lines.

### Details
- Keep wording in step with the fixture message produced by procedure 01.

## Compatibility considerations

- N/A: guidance sentence only.

## Security considerations

- N/A: no code or secret handling.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` (no findings).

## Completion criteria

- The workflow states the guarantee in one sentence and both checkers report no findings.

## Out of Scope

- Changes to `SKILL.md`, `rules/toolchain.md`, or `docs/*.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the guarantee sentence to the production-isolation paragraph | Pending | — | — | |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (state the guarantee in the test guidance)
- **Source issue**: issues/20261030-191351_flowimp006_suite-production-guard.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-075648_flowimp006_suite-production-guard.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-084616
- **Related target files**: `skills/python-test-and-fix/workflow.md`
