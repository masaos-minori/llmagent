## Goal
- Tell the Plan author where phases are written to declare a release unit for coupled phases (`REQ-001`: authoring text).

## Scope
- In scope: one bullet in Step 5's list that contains "Implementation steps MUST be small enough to be independently revertable." Out of scope: Step 3 (another Plan adds a step there) and every other section.

## Assumptions
- Step 3a: that bullet is in `## Step 5: Create the Plan` (heading at line 285, bullet at line 387 of the current file).
- Overlap (Step 2): `skills/issue-to-plan/workflow.md` is also targeted by the Plan filed from `flowimp001`. Judged compatible (plan Assumption A6): that Plan adds a step in Step 3; this row adds a bullet in Step 5.
- Depends on row 01: the bullet cites the `### Release units` block that row defines.

## Design decisions
- The bullet states the trigger (a phase breaks existing callers or tests until another phase lands, such as a `NOT NULL` column before its write path) and points to `templates/plan.md` for the entry format instead of restating it.

## Alternatives considered
N/A: single bullet.

## Implementation
### Target file
`skills/issue-to-plan/workflow.md`

### Procedure
- Insert one bullet directly after "Implementation steps MUST be small enough to be independently revertable.": when phases cannot each be validated alone, declare a release unit in the `### Release units` block of `templates/plan.md`, naming the member phases and the reason; otherwise leave the default `N/A: no release unit`.

### Method
- Use the file's existing "MUST"/bullet style; cite `templates/plan.md` by path (a reference checked by `tools/check_skills_references.py`).

### Details
- Do not add a new file reference other than `templates/plan.md`, which already exists.

## Compatibility considerations
N/A: one added bullet; no behavior changes for Plans without coupled phases.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` report no findings (AC-6).

## Completion criteria
- The bullet exists in Step 5 and both checkers pass (AC-1, AC-6).

## Out of Scope
- The template block (row 01) and the declaration check (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the declare-a-unit bullet to Step 5 | Completed | 20261102-125120 | 20261102-125120 | Stale clean; 3a bullet in Step 5 confirmed. Changed: skills/issue-to-plan/workflow.md |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` (`routing.md` Tools) | Completed | 20261102-125120 | 20261102-125120 | both skill checkers no findings; full suite deferred to plan end |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: skills/issue-to-plan/workflow.md