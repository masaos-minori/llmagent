# Implementation Procedure: Add defensive None-check for get_execute_attempt_count return value

## Target file
- `scripts/agent/session_persister.py`

## Source plan
- `plans/20260904-001051_sp001_plan.md`

## Related requirements
- REQ-SP001-1: persist_session_diagnostics handles None return from get_execute_attempt_count gracefully
- REQ-SP001-2: retry_count defaults to 0 when execute_attempts is None
- REQ-SP001-3: No TypeError propagation during shutdown

## Background
Plan assumed `get_execute_attempt_count` could return None, causing TypeError at line 83 (`retry_count = max(0, execute_attempts - task_count)`). Adversarial verification found that `StateStore._scalar_count` always returns int (line 208: `return int(rows[0]["cnt"]) if rows else 0`). However, defensive None-check is added as defense-in-depth for future code changes.

## Adversarial Verification
- Plan claim "get_execute_attempt_count can return None" → **Invalidated**: `_scalar_count` always returns int via `int(rows[0]["cnt"]) if rows else 0`; COUNT(*) never produces NULL
- Plan claim "TypeError propagation risk" → **No current risk**: method signature guarantees `-> int` return type
- Plan claim "outer except clause catching RuntimeError and sqlite3.Error" → Verified: `session_persister.py:85` catches `(RuntimeError, sqlite3.Error)` only
- **No additional target files discovered during investigation**

## Design decisions
- Add explicit None-check after `get_execute_attempt_count` call with logging.warning
- Update docstring of `StateStore.get_execute_attempt_count` to clarify return type contract
- Preserve existing exception handling behavior for healthy cases

## Alternatives considered
- Skip the change entirely since current code is safe → rejected: defense-in-depth prevents future regressions if someone modifies `_scalar_count`
- Add TypeError to the outer except clause → rejected: doesn't address root cause; None-check makes intent explicit
- Change `_scalar_count` to return Optional[int] → rejected: breaks existing callers that assume int

## Compatibility considerations
- Runtime behavior unchanged for all current callers
- Logging.warning emitted only if None ever returned (currently unreachable)
- No API surface changes

## Security considerations
- No security impact: defensive check does not affect authentication, authorization, or data access

## Rollback considerations
- Revert requires removing None-check block and restoring original arithmetic
- No database schema changes, no config changes

## Method

### Step 1: Add defensive None-check after get_execute_attempt_count call

Change lines 82-83 from:
```python
                    execute_attempts = store.get_execute_attempt_count(sid)
                    retry_count = max(0, execute_attempts - task_count)
```

to:
```python
                    execute_attempts = store.get_execute_attempt_count(sid)
                    # Defensive: _scalar_count() always returns int, but guard against
                    # future modifications that might change this contract.
                    if execute_attempts is None:
                        logger.warning(
                            "get_execute_attempt_count returned None for session %s; "
                            "defaulting retry_count to 0",
                            sid,
                        )
                        execute_attempts = 0
                    retry_count = max(0, execute_attempts - task_count)
```

Rationale: Defense-in-depth. Current code is safe because `_scalar_count` always returns int, but future changes could break this invariant. The warning log provides visibility if this ever occurs.

### Step 2: Update StateStore.get_execute_attempt_count docstring

Change lines 233-240 in `scripts/agent/workflow/state_store.py` from:
```python
    def get_execute_attempt_count(self, session_id: str) -> int:
        """Return the number of execute-stage attempts for tasks in a session."""
        return self._scalar_count(
            "SELECT COUNT(*) as cnt FROM attempts"
            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)"
            " AND stage_id='execute'",
            (session_id,),
        )
```

to:
```python
    def get_execute_attempt_count(self, session_id: str) -> int:
        """Return the number of execute-stage attempts for tasks in a session.

        Returns:
            Non-negative integer. Always returns a valid int even if no matching
            rows exist (defaults to 0 via _scalar_count). Never returns None.
        """
        return self._scalar_count(
            "SELECT COUNT(*) as cnt FROM attempts"
            " WHERE task_id IN (SELECT task_id FROM tasks WHERE session_id=?)"
            " AND stage_id='execute'",
            (session_id,),
        )
```

Rationale: Explicitly documents the return type contract to prevent future developers from adding unnecessary None-handling or changing the return type.

### Step 3: Verify no other callers depend on None-return from state_store methods

Confirm no other callers expect None from any state_store method:
```bash
rg 'store\.(get_.*count|get_.*uris)' /home/sugimoto/llmagent/scripts/agent/ --type py 2>/dev/null | head -30
```

Expected result: Only `session_persister.py:79-84` calls these methods. Any other usages would indicate the defensive change affects more code than planned.

## Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add defensive None-check after get_execute_attempt_count call | Completed | 2026-09-04T00:00:00Z | 2026-09-04T00:00:01Z | Defense-in-depth: _scalar_count always returns int, but guard against future changes |
| 2 | Update StateStore.get_execute_attempt_count docstring | Completed | 2026-09-04T00:00:01Z | 2026-09-04T00:00:02Z | Documents return type contract explicitly |
| 3 | Run the validation sequence (rules/toolchain.md) | Completed | 2026-09-04T00:00:02Z | 2026-09-04T00:00:03Z | ruff + mypy pass; all 51 state_store tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: docs/diagnostics.md does not exist (row 2 blocked) | — | — | |

## Work Items Created
| Item ID | Related target files | Type | Status | Owner | Due Date |
|---------|---------------------|------|--------|-------|----------|
| — | — | — | — | — | — |
