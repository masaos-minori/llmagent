## Goal
- Make the Step 10 row of the phase table refer to the `repo_scan` rule in `workflow.md` Step 10 (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: row 10 of the phase table.
- Not in scope: the isolation bullet that holds the production-safety default expression.

## Assumptions
- Row 10 says to run `pytest --testmon-forceselect` together with `-m` and that the single full run in Step 11 is unchanged; the isolation bullet holds the safety default and stays as it is. Falsifier: row 10 already states the rule.

## Design decisions
- One reference, no restatement of the rule.

## Alternatives considered
N/A: a reference is the only choice (single statement in `workflow.md` Step 10).

## Implementation
### Target file
`skills/python-test-and-fix/SKILL.md`

### Procedure
1. Append to row 10 a clause saying iteration runs also deselect the whole-repository scans marked `repo_scan` and that `workflow.md` Step 10 states the rule.
2. Run the two skill checkers.

### Method
Edit the table cell in place, keeping it one line.

### Details
- Do not repeat which commands exclude the marker.
- Do not edit the `-m` default sentence in the isolation bullet.

## Compatibility considerations
N/A: skill text only.

## Security considerations
N/A: no security impact.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py`.
- `uv run python tools/run_validation_gates.py`.

## Completion criteria
- Row 10 refers to `workflow.md` Step 10 for the marker rule and the isolation bullet is unchanged (`AC-004`).

## Out of Scope
- The rule text itself, other rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-132153 | 20261113-132924 | Changed skills/python-test-and-fix/SKILL.md: row 10 of the phase table gained one sentence saying iteration runs also deselect the whole-repository scans marked repo_scan and pointing to workflow.md Step 10 for the rule (a reference, not a restatement). The isolation bullet with the production-safety default expression is unchanged. |
| 2 | Run the skill checkers named in Validation plan (`routing.md` Tools "When to run which tool") | Completed | 20261113-132924 | 20261113-132924 | check_skills_references and check_skills_heading_cycles: No issues found; run_validation_gates exit 0 with no Fail or Blocked. Full suite serial 12151 passed, 3 failed: the known mdq cases (unrelated, Plan testspeed004); diff-cover N/A: no source file changed. |

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
- **Requirement ID**: REQ-005 (consistent reference from the skill summary)
- **Source issue**: issues/20261112-183738_testspeed001_mark-repo-scan-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261113-093307_testspeed001_mark-repo-scan-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261113-102218
- **Related target files**: `skills/python-test-and-fix/SKILL.md`
