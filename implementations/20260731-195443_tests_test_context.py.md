# Implementation Procedure: Concurrency Tests for TurnState

## Goal
Verify that `TurnState` correctly handles concurrent access using `asyncio.Lock`.

## Scope
- In scope:
  - Creation of `tests/test_context.py`.
  - Test cases for concurrent `add_tool_call` operations.
- Out of scope:
  - Testing other parts of the agent context.

## Assumptions
- `pytest` and `pytest-asyncio` are installed and configured in the environment.
- `TurnState` is accessible for testing.

## Design decisions
- Use `asyncio.gather` to trigger multiple concurrent `add_tool_call` requests.
- Assert that the final count of `tool_calls` matches the number of requested additions.

## Implementation
### Target file
`tests/test_context.py`

### Procedure
1. Create `tests/test_context.py`.
2. Define `test_turn_state_concurrency` as an async test.
3. Instantiate `TurnState`.
4. Launch $N$ concurrent `add_tool_call` tasks using `asyncio.gather`.
5. Assert `len(turn_state.get_tool_calls()) == N`.
6. Assert `turn_state.turn_count == N`.

### Method
Automated unit testing using `pytest-asyncio` to stress-test the locking mechanism in `TurnState`.

### Details
The test will focus on ensuring that even when many coroutines attempt to update the `tool_calls` list simultaneously, no updates are lost due to race conditions.

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
Delete the newly created `tests/test_context.py`.

## Validation plan
Run `uv run pytest tests/test_context.py`.

## Out of scope
- Performance benchmarking of the lock.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260731-090123_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-195443
- Related target files: tests/test_context.py
