# ApprovalRecovery: Overwrites pending_approval_task_id without synchronization

## Background

`ApprovalRecovery.recover()` in `scripts/agent/startup_approval_recovery.py` restores workflow approval-pending state from a previous session during startup. It sets `ctx.turn.pending_approval_task_id` to the most recent pending approval's task ID.

## Problem

The method overwrites `pending_approval_task_id` without checking whether the Orchestrator has already set it for a different approval. The warning log is emitted but the overwrite proceeds regardless.

## Evidence

- File: `scripts/agent/startup_approval_recovery.py`
- Lines 50-56:

```python
if ctx.turn.pending_approval_task_id is not None:
    logger.warning(
        "Overwriting pending_approval_task_id %s with %s during recovery",
        ctx.turn.pending_approval_task_id,
        task_id,
    )
ctx.turn.pending_approval_task_id = task_id  # Always overwrites
```

## Impact

- If the Orchestrator has already set `pending_approval_task_id` for a different approval, the recovery silently overwrites it
- The user sees the wrong approval wired up for immediate action
- Inconsistent state between what the user expects and what the system acts on

## Recommended action

1. Only overwrite if the current value is stale (from a previous session).
2. Compare the recovered task ID against the current value and prefer the newer one.
3. Alternatively, require explicit user confirmation before auto-wiring a recovered approval.

```python
current_task_id = ctx.turn.pending_approval_task_id
if current_task_id is not None and current_task_id != task_id:
    logger.warning(
        "Overwriting pending_approval_task_id %s with %s during recovery",
        current_task_id,
        task_id,
    )
    # Prefer the currently active approval if it exists
    if self._is_current_approval(current_task_id):
        logger.info("Keeping current pending_approval_task_id: %s", current_task_id)
        return
ctx.turn.pending_approval_task_id = task_id
```

## Acceptance criteria

- [ ] Recovery does not overwrite an active approval without justification
- [ ] Test verifies recovery respects existing approval state
- [ ] Test verifies recovery correctly overwrites stale state
- [ ] Warning message includes both old and new values

## Out of scope

- Changes to the approval recovery query logic
- Changes to the StateStore API
