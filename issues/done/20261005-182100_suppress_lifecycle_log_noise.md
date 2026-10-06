# Fix same-state lifecycle transitions during shutdown

## Summary

During shutdown, MCP servers attempt invalid state transitions (e.g., STOPPED→STOPPED). These are legitimate errors from the lifecycle state machine but occur during normal shutdown and do not indicate a real problem.

## Background

The `LifecycleManager` logs warnings when a state transition is invalid. During shutdown, some MCP servers attempt transitions that are invalid per the lifecycle state machine (e.g., STOPPED→STOPPED is not in the valid targets `{STARTING, FAILED}`). The state machine explicitly disallows same-state transitions.

## Problem

Shutdown output includes messages like:
```
Lifecycle: invalid state transition <LifecycleState.STOPPED: 'stopped'> -> <LifecycleState.STOPPED: 'stopped'> for 'X'
```

These occur because the lifecycle state machine does not allow same-state transitions (STOPPED→STOPPED is not in the valid targets `{STARTING, FAILED}`).

## Reason for Change

These messages are harmless during shutdown but indicate a mismatch between the lifecycle state machine and shutdown behavior. Two approaches are possible:
1. Suppress same-state transition warnings (quick fix, changes semantics)
2. Add same-state transitions to the valid transitions table (correct fix, preserves semantics)

## Implementation Intent

Two options:

### Option A: Suppress same-state transition warnings (quick fix)

Modify the lifecycle state transition logging to suppress warnings for same-state transitions:

```python
# Before:
logger.warning("Lifecycle: invalid state transition %r -> %r for %r", old_state, new_state, name)

# After:
if old_state != new_state:
    logger.warning("Lifecycle: invalid state transition %r -> %r for %r", old_state, new_state, name)
```

### Option B: Add same-state transitions to valid transitions (correct fix)

Add same-state transitions to the `_VALID_TRANSITIONS` table in `scripts/agent/lifecycle.py`:

```python
_LIFECYCLE_STATE: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.STOPPED: frozenset({LifecycleState.STARTING, LifecycleState.FAILED, LifecycleState.STOPPED}),
    # ... etc.
}
```

This is the preferred approach — it makes the state machine semantically correct rather than hiding the inconsistency.

## Target Files or Areas

- `scripts/agent/factory.py` — line 222 (Option A only)
- `scripts/agent/lifecycle.py` — `_VALID_TRANSITIONS` table (Option B)

## Required Changes

Add a check to skip logging for same-state transitions:
```python
# Before:
logger.warning("Lifecycle: invalid state transition %r -> %r for %r", old_state, new_state, name)

# After:
if old_state != new_state:
    logger.warning("Lifecycle: invalid state transition %r -> %r for %r", old_state, new_state, name)
```

## Constraints

- Option A: Do not suppress legitimate state transition errors; only suppress same-state transitions
- Option B: Preserve existing valid transitions; only add same-state transitions
- Neither option should change the lifecycle state machine logic for non-same-state transitions

## Out of Scope

- Changing the lifecycle state machine logic
- Modifying other lifecycle management behavior
- Adding new lifecycle states

## Dependencies

- N/A: none

## Acceptance Criteria

- [ ] No duplicate STOPPED→STOPPED transition messages during shutdown
- [ ] Legitimate invalid state transitions still produce warnings
- [ ] Shutdown completes normally

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and Ctrl+C to trigger shutdown
- Verify no duplicate STOPPED→STOPPED messages appear

## Documentation Impact

N/A: no documentation update required

## Unresolved Questions

- N/A: the fix is straightforward

## Evidence

- Shutdown output: invalid state transition messages for same-state transitions
- Source: `scripts/agent/factory.py:219-226` (logging invalid transitions)
- Source: `scripts/agent/lifecycle.py:33-43` (`_VALID_TRANSITIONS` table — STOPPED→STOPPED not allowed)
- Source: `scripts/agent/lifecycle.py:46-58` (`assert_valid_transition` function)

## Priority

Low
