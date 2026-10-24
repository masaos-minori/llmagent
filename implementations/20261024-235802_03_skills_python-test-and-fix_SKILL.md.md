## Goal
- Align Phase overview row 10 of `skills/python-test-and-fix/SKILL.md` with the corrected Step 10 (`REQ-005`: correct the testmon wording).

## Scope
- Row 10 only (line 83 at time of writing): `| 10 | Impact-based execution | Leverage pytest-testmon if available for rapid, incremental test execution during local feedback loops. |`.

## Assumptions
- Row text confirmed 2026-10-24. `pytest-testmon>=2.1` is declared in `pyproject.toml` (line 61), so "if available" is replaced by the condition that actually applies: testmon is installed and `.testmondata` is not in use by another session.
- The corrected Step 10 wording comes from row `02` (`skills/python-test-and-fix/workflow.md`); this row is applied after it.

## Design decisions
- One-line rewrite: iterate with `--testmon-forceselect` together with `-m` (plain `--testmon` is deactivated by `-m`); the single full run in Step 11 is unchanged.

## Alternatives considered
N/A: single table-row wording edit.

## Implementation
### Target file
`skills/python-test-and-fix/SKILL.md`

### Procedure
1. Rewrite the row-10 description cell to match Step 10, keeping the table on one line per row.

### Method
- Edit in place with the row text as `old_string`.

### Details
- Do not change the Step 11 row or the `No Tool Hallucination` bullet.

## Compatibility considerations
N/A: wording only.

## Security considerations
N/A: instruction text only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` exit 0.

## Completion criteria
- Row 10 no longer says "if available" and matches Step 10; both checkers exit 0.

## Out of Scope
- Other Phase overview rows and `workflow.md`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite Phase overview row 10 | Pending | — | — | |
| 2 | Run both skills checkers | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (correct testmon wording)
- **Source issue**: issues/20261024-203550_perf004_bound-verification-sequence-cost.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261024-233036_bound-verification-sequence-cost.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261024-235802
- **Related target files**: `skills/python-test-and-fix/SKILL.md`
