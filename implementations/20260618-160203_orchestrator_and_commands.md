# Implementation: Orchestrator workflow-first + CLI approval commands

## Goal

- Update `Orchestrator.handle_turn()` to use optional session_id/turn_number
- Handle `WorkflowPendingApprovalError` in orchestrator
- Add `/approve` and `/reject` slash commands

## Scope

- `scripts/agent/orchestrator.py`
- `scripts/agent/commands/` — new `cmd_workflow.py` or extend existing registry

## Details

### orchestrator.py

`create_task()` call: remove positional session_id/turn_number; pass as kwargs.

Handle `WorkflowPendingApprovalError`:
```python
except WorkflowPendingApprovalError as exc:
    logger.info("Turn suspended: awaiting approval %s", exc.approval_id)
    if self._on_error:
        self._on_error(exc)
```

Store `approval_id` on `ctx.turn` for use by `/approve`/`/reject`:
```python
ctx.turn.pending_approval_id = exc.approval_id
```

### commands — /approve and /reject

New methods in appropriate command mixin (e.g. `cmd_workflow.py`):
- `/approve [reason]` — calls `store.resolve_approval(approval_id, "approved", reason)`
- `/reject [reason]` — calls `store.resolve_approval(approval_id, "rejected", reason)`

Both read `ctx.turn.pending_approval_id`; error if None.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/orchestrator.py scripts/agent/commands/` | 0 errors |
| Type | `uv run mypy scripts/agent/orchestrator.py scripts/agent/commands/` | no new errors |
| Tests | `uv run pytest tests/ -k "workflow or approval" -v` | all pass |
