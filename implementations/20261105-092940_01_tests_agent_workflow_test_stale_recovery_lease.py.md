## Goal
- Correct the `TestFencingGateAC7` docstring so every path it cites exists and it states the gate's current meaning, and confirm the suppression checker stays at 0 issues (`REQ-001`: docstring provenance; `REQ-002`: comment-level change only).

## Scope
**Release unit**: N/A: not part of a release unit
- Docstring of one test class in `tests/agent/workflow/test_stale_recovery_lease.py`. The two suppression lines the Issue named are already justified (checker reports `All checks passed`) and are not touched.

## Assumptions
- `AttemptFencedError` is still absent from `scripts/`, so the gate test's premise holds.
- The four cited paths exist: `issues/done/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`, `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`, `implementations/done/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md` (the conditional `finish_attempt` procedure), and `implementations/done/20261101-163219_12_tests_agent_workflow_test_stale_recovery_lease.py.md`.

## Design decisions
- State only verified facts: the fence is not yet implemented, and name the artifacts that carry it. Do not claim who will implement it (Plan UNK-01).

## Alternatives considered
- N/A: docstring-only edit.

## Implementation
### Target file
`tests/agent/workflow/test_stale_recovery_lease.py`

### Procedure
1. Replace the first docstring line "gated on the wfrecovery001 plan (Pending in plans/done/)" with a statement that the fence is not yet implemented and is specified by the wfrecovery001 Plan.
2. Replace the closing "See implementations/done/20261031-212239_wfrecovery001_recovery-dag.md." with a "See:" list of the four existing paths named in Assumptions.

### Method
- Keep the middle sentences ("`AttemptFencedError` and the finish_attempt fence do not exist ... flipped into a passing enforcement gate") as they are.
- Keep the class, its tests, and the `# noqa: F401 — ...` line unchanged; do not reflow code.

### Details
- Check each cited path with `ls` after editing; a path that does not exist is a defect of this change.

## Compatibility considerations
- N/A: comment-level change.

## Security considerations
- N/A: comment-level change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_suppression_justification.py` reports 0 issues.
- `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py tests/shared/test_json_utils.py`; `uv run ruff check tests/agent/workflow/test_stale_recovery_lease.py`.
- `git diff` shows only docstring lines changed.

## Completion criteria
- Every path in the docstring resolves, the checker reports 0 issues, both test files pass, and the diff touches only the docstring.

## Out of Scope
- Implementing the fence, other suppression audits, and `tests/shared/test_json_utils.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the `TestFencingGateAC7` docstring references | Pending | — | — | |
| 2 | Run the suppression checker, the two test files, and `ls` on each cited path | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (correct docstring citations), `REQ-002` (comment-level change, checker clean)
- **Source issue**: issues/20261103-134148_wfreview005_unjustified-suppressions-and-stale-test-provenance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261105-090126_wfreview005_unjustified-suppressions-and-stale-test-provenance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-092940
- **Related target files**: `tests/agent/workflow/test_stale_recovery_lease.py`
