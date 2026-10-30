## Goal

Test that the tool runner sets the per-attempt side-effect flag only for non-READ calls, on both the gateway and the no-gateway path, in `tests/agent/test_tool_runner.py` (`REQ-006`, side-effect flag; `REQ-009`, tests).

## Scope

- Modify only `tests/agent/test_tool_runner.py`.

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 3 test, written with rows 06 and 07; independent of the wfrecovery001 Plan. Execution order follows the Plan's phases, not `seq`.
- The file's classes (`TestExecuteWithDag` at `:251`, `TestExecuteOneToolCallRecordsOnGuard` at `:560`, and others) build an `AgentContext` with a stub gateway or tool executor; `_execute_prepared_call` is not referenced directly by any test today, so the new tests drive it through the same entry points the existing classes use.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `side_effects_started` (row 06 document).

## Design decisions

- Add one small test class with three cases built on the existing context fixtures: a non-READ call through the gateway sets the flag; a READ call leaves it false; a non-READ call without a gateway sets it as well.

## Alternatives considered

- N/A: test row.

## Implementation

### Target file

`tests/agent/test_tool_runner.py`

### Procedure

1. Add the three cases above, asserting `ctx.turn.side_effects_started` after the call completes, and in a variant where the call raises (the flag stays set).
2. Use a write tool name from the static write set (for example one in `scripts/agent/tool_policy.py`'s write tools) and a registry-classified READ tool for the READ case.

### Method

- Reset the flag to false at the start of each case so cases are independent.

### Details

- Write the tests first and confirm they fail before row 07 is implemented.

## Compatibility considerations

- N/A: tests only.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py -v`
- `uv run ruff format tests/agent/test_tool_runner.py`, `uv run ruff check tests/agent/test_tool_runner.py`

## Completion criteria

- The cases pass after row 07 and fail before it.

## Out of Scope

- The retry rule built on the flag (rows 01 and 08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the flag tests | Pending | — | — | Plan Phase 3 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-006, REQ-009 (side-effect flag tests)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: tests/agent/test_tool_runner.py
