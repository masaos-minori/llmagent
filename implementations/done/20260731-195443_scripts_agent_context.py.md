# Implementation Procedure: Concurrency Control in TurnState

## Goal
Add explicit concurrency control using `asyncio.Lock` to protect shared state in `TurnState`.

## Scope
- In scope:
  - Modifying `TurnState` in `scripts/agent/context.py` to include an `asyncio.Lock`.
  - Encapsulating mutable fields of `TurnState` within async methods.
  - Updating all callers of `TurnState` to use these new async methods.
- Out of scope:
  - Any changes to other classes in `AgentContext`.
  - Changing the fundamental behavior of `Orchestrator` or `AgentREPL`.

## Assumptions
- The current `TurnState` class is a `@dataclass` with public mutable attributes.
- Multiple coroutines (e.g., from `Orchestrator`, `CommandRegistry`, etc.) access and modify `TurnState` concurrently.
- Adding `asyncio.Lock` and changing field access to method calls is sufficient to prevent race conditions.

## Design decisions
- **Encapsulation**: Convert `TurnState` from a `@dataclass` to a regular class to allow initialization of `self._lock = asyncio.Lock()` in `__init__`.
- **Async Interface**: All modifications to `TurnState`'s internal state (like `tool_calls`, `turn_count`, etc.) must be performed via `async def` methods that acquire the lock.
- **Read Access**: Provide `async def` getter methods for fields that require consistency during read (e.g., returning a copy of a list).

## Alternatives considered
- Using `threading.Lock`: Rejected because the system is single-threaded but uses `asyncio` for concurrency; `asyncio.Lock` is appropriate for coroutine synchronization.

## Implementation
### Target file
`scripts/agent/context.py`

### Procedure
1. Import `asyncio` at the top of `scripts/agent/context.py`.
2. Redefine `TurnState` as a standard Python class.
3. Implement `__init__` to initialize all existing fields and add `self._lock = asyncio.Lock()`.
4. Implement `async def add_tool_call(self, call_id: str)` which appends to `tool_calls` and increments `turn_count` under lock.
5. Implement `async def get_tool_calls(self) -> list[str]` which returns `list(self.tool_calls)` under lock.
6. Identify all direct attribute accesses to `TurnState` in the codebase (e.g., `ctx.turn.current_turn_id`, `ctx.turn.pending_approval_id`) and replace them with appropriate async method calls or ensure they are safe if they are read-only. *Note: For simple reads of immutable/atomic types like `str | None`, direct access might remain if no race condition is possible, but for lists/counters, methods are required.*
7. Verify that all updates to `TurnState` are now wrapped in `async with self._lock`.

### Method
Refactoring `TurnState` to encapsulate its state and provide an asynchronous API for thread-safe (coroutine-safe) operations.

### Details
The primary target is protecting `tool_calls` (a list) and `turn_count` (an integer) from race conditions during simultaneous updates from different tasks in the `Orchestrator` loop and command handlers.

## Compatibility considerations
N/A

## Security considerations
N/A

## Rollback considerations
Revert `TurnState` back to a `@dataclass` and restore direct attribute access in all caller sites.

## Validation plan
- Unit tests in `tests/test_context.py` simulating concurrent calls to `add_tool_call`.
- Integration tests verifying `Orchestrator` turn processing flow remains intact.

## Out of scope
- Refactoring `RuntimeStats` or `WorkflowState` for similar concurrency needs unless discovered during implementation.

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260731-070929_require.md
- Source plan: plans/20260731-090123_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-195443
- Related target files: scripts/agent/context.py
