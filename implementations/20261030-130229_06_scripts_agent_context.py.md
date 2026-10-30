## Goal

Add a per-attempt side-effect flag to `TurnState` in `scripts/agent/context.py` (`REQ-006`, a place to record that a non-READ tool call executed in the attempt).

## Scope

- Modify only `scripts/agent/context.py` (the `TurnState` dataclass).

## Assumptions

- Plan Dependencies (`plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` Scope): Plan Phase 3; independent of the other phases; it must exist before rows 05 (adapter) and 07 (tool runner) are executed. Execution order follows the Plan's phases, not `seq`.
- Verified in Step 3 of the Plan: `TurnState` (`context.py:213-226`) has no side-effect record; its docstring says per-turn state is reset each turn, but its field comment says it is constructed once with `AgentContext` and not reset between turns, so the adapter (not the orchestrator) clears the flag at each attempt start.
- `context.py` has 12 commits in the last 30 days (high churn); keep the change to one field.

## Design decisions

- Add `side_effects_started: bool = False` with a short comment naming its writer (`tool_runner`) and its reset point (attempt start in the adapter).

## Alternatives considered

- Track tool call ids per attempt: rejected, a yes or no flag satisfies the rule (Plan Design).

## Implementation

### Target file

`scripts/agent/context.py`

### Procedure

1. Add the `side_effects_started` field to `TurnState` (`:213`), after `persistence_boundary`.

### Method

- A plain defaulted boolean field; no logic in the dataclass.

### Details

- No other dataclass in this module changes.

## Compatibility considerations

- Additive, defaulted field; existing constructions of `TurnState` stay valid.

## Security considerations

- N/A.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/test_tool_runner.py tests/agent/test_orchestrator.py -v`
- `uv run ruff format scripts/agent/context.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- `TurnState().side_effects_started` is `False`.

## Out of Scope

- Setting and clearing the flag (rows 07 and 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `side_effects_started` field | Pending | — | — | Plan Phase 3 |
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
- **Requirement ID**: REQ-006 (side-effect flag on the turn state)
- **Source issue**: issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130229
- **Related target files**: scripts/agent/context.py
