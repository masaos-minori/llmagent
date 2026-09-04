# Implementation Procedure: Unify cancellation paths for _input_coro in REPL input loop

## Target file
- `scripts/agent/repl_input_loop.py`

## Source plan
- `plans/20260904-001051_ril001_plan.md`

## Related requirements
- REQ-RIL001-1: Only one cancellation path for _input_coro during shutdown
- REQ-RIL001-2: Consistent error message regardless of shutdown trigger

## Background
`ReplInputLoop._read_input` has two concurrent cancellation paths for `_input_coro`:
1. `signal_handler.py:_sigterm_handler` directly calls `self._input_coro.cancel()` (lines 49-57)
2. `repl_input_loop.py:_read_input` cancels pending tasks via `for t in pending: t.cancel()` (lines 130-131)

This causes non-deterministic exception propagation through `input_coro.result()`, making debugging difficult.

## Adversarial Verification
- Plan claim "signal_handler.py:49-57 has _input_coro.cancel()" → Verified: lines 49-57 confirm `_sigterm_handler` calls `self._input_coro.cancel()` under guard conditions
- Plan claim "repl_input_loop.py:130-131 cancels pending tasks" → Verified: lines 130-131 confirm `for t in pending: t.cancel()` after `asyncio.wait(FIRST_COMPLETED)`
- No additional target files discovered during investigation

## Design decisions
- Choose shutdown watcher as single source of cancellation because it already tracks `shutdown_done` state
- Remove signal handler's direct `_input_coro.cancel()` call — `shutdown_event.set()` triggers shutdown watcher which handles cleanup
- Preserve existing `CancelledError` handling in `_read_input` for robustness during transition

## Alternatives considered
- Keep signal handler as single source, remove shutdown watcher cancellation → rejected: shutdown watcher already has `shutdown_done` tracking, simpler to extend
- Introduce explicit coordination protocol between both paths → rejected: adds complexity without clear benefit over simple delegation

## Compatibility considerations
- Signal handler's `loop.add_signal_handler` registration unchanged
- `_abort_input()` behavior preserved
- `shutdown_done` flag semantics unchanged

## Security considerations
- No security impact: cancellation logic change does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires restoring both modifications: re-add `_input_coro.cancel()` in signal_handler.py and restore `for t in pending: t.cancel()` in repl_input_loop.py
- No database schema changes, no config changes

## Method

### Step 1: Modify `_read_input` in repl_input_loop.py

#### 1.1 Remove duplicate cancellation in the `try/except` block

Change lines 130-131 from:
```python
            for t in pending:
                t.cancel()
```
to:
```python
            # Cancellation handled by shutdown watcher — do not cancel here
```

Rationale: The shutdown watcher (`_shutdown_watcher`) sets `shutdown_done=True` when shutdown occurs. The subsequent check at lines 132-134 uses this flag to determine whether to abort input. Direct cancellation of pending tasks creates a race condition where `_input_coro` may be cancelled before the shutdown watcher completes its coordination.

#### 1.2 Preserve CancelledError handling for robustness

Keep lines 137-140 as-is:
```python
            except asyncio.CancelledError:
                # Input was cancelled by signal handler — treat as shutdown
                self._abort_input()
                return None
```

Rationale: Even after removing the duplicate cancellation path, this handler provides defense-in-depth. If any future code path cancels `_input_coro`, this ensures consistent shutdown behavior.

### Step 2: Update class docstring

Add documentation about the shutdown coordination mechanism to `ReplInputLoop.__init__` docstring (around line 27-31):

After the existing docstring text, add:
```
    Shutdown coordination:
        - shutdown_event is the single source of truth for shutdown signaling
        - _shutdown_watcher sets shutdown_done when shutdown_event fires
        - _read_input checks shutdown_done to decide whether to abort input
        - Signal handler delegates cancellation to shutdown_event.set() (see signal_handler.py)
```

### Step 3: Verify no other callers of _input_coro.cancel() exist

Search for all references to `_input_coro.cancel()` across the codebase:
```bash
rg '_input_coro\.cancel' scripts/agent/
```

If any additional callers are found beyond `signal_handler.py`, report `Blocked: additional target file discovered` per workflow rules.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1.1 | Remove duplicate cancellation in _read_input | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Replaced with comment; single cancellation path via shutdown watcher |
| 1.2 | Preserve CancelledError handling | Not needed | — | — | CancelledError handler was already preserved |
| 2 | Update class docstring | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Documents shutdown coordination mechanism |
| 3 | Verify no other callers | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | Only 1 caller in signal_handler.py; ruff + mypy pass |

## Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |
