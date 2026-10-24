## Goal
- Correct the remaining plain-`--testmon` forms in `skills/python-test-and-fix/workflow.md` Step 10 and add the note that `-m` deactivates plain `--testmon` selection (`REQ-005`: correct the testmon commands and wording).

## Scope
- Step 10 only (lines 368-390 at time of writing): the opening prose, the `MUST NOT re-run` sentence, and the first command line of the bash block.

## Assumptions
- Step 10 already has the `--testmon-noselect` and `--testmon-forceselect -m ...` lines and their description (lines 385-390); they stay as written.
- Still wrong at line 370 (`Use pytest --testmon while iterating`), line 378 (`MUST NOT re-run pytest --testmon`), and line 384 (`--testmon -m ...`, commented "only tests affected by changed files"). Measured 2026-10-24: with `-m`, plain `--testmon` prints "selection automatically deactivated because -m was used" and runs everything.
- Another session edited this file earlier on 2026-10-24 (commits `09c9ff39d`, `b652c6bf9`, `bb4407725`); re-read and re-anchor immediately before editing.
- `skills/code-implementation/workflow.md` Step 4 (row `01`) cites this Step 10 by name; the two rows can be applied in either order.

## Design decisions
- Replace the plain form in the iteration command with `--testmon-forceselect -m "not integration and not production_paths_allowed" tests/`, and add one sentence: plain `--testmon` is deactivated whenever `-m` is given, so it runs every test.

## Alternatives considered
N/A: wording and example correction decided in the Plan Design.

## Implementation
### Target file
`skills/python-test-and-fix/workflow.md`

### Procedure
1. Line 370 prose: say iteration uses `--testmon-forceselect` together with `-m`.
2. Line 378: change the idempotent-run sentence to name `--testmon-forceselect`.
3. Line 384: change the first command to `--testmon-forceselect` or remove it as a duplicate of line 386, keeping exactly one forceselect line.
4. Add the "`-m` deactivates plain `--testmon`" note next to the `--testmon-noselect` description.

### Method
- Edit in place with unique `old_string` values; keep the noselect line and its description.

### Details
- Do not alter the full-suite command, the `pgrep` pre-check, or the `.testmondata` ignore rule.

## Compatibility considerations
- `skills/code-implementation/workflow.md` Step 4 cites this Step; its wording is updated in row `01`.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.
- `rg -n "testmon" skills/python-test-and-fix/workflow.md` shows no plain `--testmon ... -m` example.

## Completion criteria
- No example combines plain `--testmon` with `-m`; the deactivation note exists; both checkers exit 0.

## Out of Scope
- Other Steps of the file, the full-suite instructions, and `.gitignore` rules.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the Step 10 prose and command lines and add the deactivation note | Completed | — | 20261025-003436 |  |
| 2 | Run both skills checkers and the `rg` check | Completed | — | 20261025-003436 |  |

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
- **Requirement ID**: `REQ-005` (correct testmon commands and wording)
- **Source issue**: issues/20261024-203550_perf004_bound-verification-sequence-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-233036_bound-verification-sequence-cost.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235802
- **Related target files**: `skills/python-test-and-fix/workflow.md`