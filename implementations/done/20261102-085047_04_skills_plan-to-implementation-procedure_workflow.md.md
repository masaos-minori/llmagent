## Goal
- Make the generation workflow copy the unit name into each procedure's `Release unit` line (`REQ-002`: carry the unit name).

## Scope
- In scope: one bullet in Step 3c. Out of scope: Step 1, Step 2, the Step 3c additional-discovery and item (2) text, and the Step 4 checklist and `Work Items Created` text (other Plans edit them).

## Assumptions
- Step 3a: Step 3c's bullet list ends with "Apply `rules/workflow-lifecycle.md` Requirement Reference Format ..." and a "Judge each row against the template's Lightweight fill" bullet; the new bullet goes between them.
- Overlap (Step 2): this file is also targeted by the Plans filed from `flowimp003` (Step 2 and a gated marker in Step 4), `flowimp007` (Step 3c item (2)), `flowimp008` (Step 4 `Work Items Created`), `flowimp009` (Step 3c one-document text and the Step 4 checklist), and `flowimp011` (Step 3c additional-discovery paragraph). Judged compatible (plan Assumption A7 and the other Plans' own Assumptions): each edits a different paragraph; this row adds one new bullet and touches none of them. Whichever lands later rebases.
- The row-02 `Release unit` line must exist for the instruction to make sense; rows run in `seq` order.

## Design decisions
- The bullet: find the `Implementation steps` entry that cites this row's `File Path`; if that step number is listed in a `### Release units` entry of the Plan, write that unit's name on the document's `Release unit` line; otherwise leave the default `N/A: not part of a release unit`.
- No Step 4 checklist change: the line is informational for `code-implementation` and has no move gate.

## Alternatives considered
N/A: single bullet; a Step 4 gate was left out to avoid the paragraph `flowimp009` edits.

## Implementation
### Target file
`skills/plan-to-implementation-procedure/workflow.md`

### Procedure
- Insert the bullet in Step 3c's `Not implemented` handling list, after the Requirement Reference Format bullet.

### Method
- State: the step-to-row mapping is the one Step 4 already uses (a step modifies a cited `File Path`); a row cited by no step is already a `Plan Gap` there, so no new failure mode is added.

### Details
N/A: covered by Procedure and Method.

## Compatibility considerations
- Plans without a declaration produce the default line, so existing behavior is unchanged.

## Security considerations
N/A: documentation only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py`; `uv run python tools/check_skills_heading_cycles.py` report no findings (AC-6).

## Completion criteria
- The bullet exists in Step 3c and both checkers pass (AC-1, AC-6).

## Out of Scope
- The template line (row 02) and the batch-mode reader (row 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the copy-the-unit-name bullet to Step 3c | Completed | 20261102-125133 | 20261102-125133 | Stale clean; 3a anchors confirmed. Changed: skills/plan-to-implementation-procedure/workflow.md |
| 2 | Run `check_skills_references.py` and `check_skills_heading_cycles.py` | Completed | 20261102-125133 | 20261102-125133 | both skill checkers no findings; full suite deferred to plan end |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/20261030-191057_flowimp002_plan-release-units.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261102-080336_flowimp002_plan-release-units.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261102-085047
- **Related target files**: skills/plan-to-implementation-procedure/workflow.md