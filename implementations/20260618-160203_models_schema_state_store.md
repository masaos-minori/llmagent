# Implementation: approval state model + schema + state_store CRUD

## Goal

- Add `ApprovalRecord` dataclass to `models.py`
- Make `TaskRecord.session_id` and `turn_number` optional
- Add `approvals` table to `workflow_schema.py`
- Add approval CRUD to `state_store.py`

## Scope

- `scripts/agent/workflow/models.py`
- `scripts/db/workflow_schema.py`
- `scripts/agent/workflow/state_store.py`
- `scripts/agent/workflow/__init__.py`

## Details

### models.py — ApprovalRecord + optional fields

`TaskRecord.session_id: str` → `str | None`
`TaskRecord.turn_number: int` → `int | None`

New dataclass:
```python
@dataclass
class ApprovalRecord:
    approval_id: str
    task_id: str
    stage_id: str | None    # None = task-level gate
    status: str             # pending | approved | rejected
    reason: str | None      # rejection reason or approval note
    created_at: str
    resolved_at: str | None
```

### workflow_schema.py — approvals table + nullable columns

```sql
ALTER TABLE tasks — NOT applied (SQLite ALTER is limited); new installs get nullable via schema change
```

Schema change: `session_id TEXT` (remove NOT NULL), `turn_number INTEGER` (remove NOT NULL).

New table:
```sql
CREATE TABLE IF NOT EXISTS approvals (
    approval_id  TEXT PRIMARY KEY,
    task_id      TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id     TEXT,          -- NULL = task-level gate
    status       TEXT NOT NULL DEFAULT 'pending',
    reason       TEXT,
    created_at   TEXT NOT NULL,
    resolved_at  TEXT
);
```

### state_store.py — approval CRUD

New methods on `StateStore`:
- `request_approval(task_id, stage_id=None) -> ApprovalRecord`
- `resolve_approval(approval_id, status, reason=None) -> None`  (status: approved|rejected)
- `get_pending_approval(task_id) -> ApprovalRecord | None`

`create_task()` signature change:
```python
def create_task(
    self,
    workflow_version: str,
    session_id: str | None = None,
    turn_number: int | None = None,
) -> TaskRecord:
```
`idempotency_key` = `f"{session_id}:{turn_number}"` when both are set, else `str(uuid4())`

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/workflow/models.py scripts/db/workflow_schema.py scripts/agent/workflow/state_store.py` | 0 errors |
| Type | `uv run mypy scripts/agent/workflow/models.py scripts/db/workflow_schema.py scripts/agent/workflow/state_store.py` | no new errors |
| Tests | `uv run pytest tests/test_workflow_models.py tests/test_workflow_state_store.py tests/test_workflow_schema.py -v` | all pass |
