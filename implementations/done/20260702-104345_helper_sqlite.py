# Implementation: SQLiteHelper - Support eventbus target

## Goal

Update SQLiteHelper to resolve eventbus_db_path and ensure _default_load_vec is False for eventbus.

## Scope

- SQLiteHelper.__init__ method: add eventbus path resolution, update error message, update _default_load_vec logic

## Assumptions

1. Event Bus does NOT need sqlite-vec extension loaded (only RAG needs it)
2. The parent directory validation in DbConfig.__post_init__ already handles this case consistently
3. No special connection pragmas needed for eventbus beyond the defaults

## Implementation

### Target file

- `scripts/db/helper.py`

### Procedure

1. Update error message in __init__ to include "eventbus"
2. Add eventbus path resolution in the if/elif chain
3. Update _default_load_vec logic so eventbus does NOT load vec by default

### Method

- Follow existing pattern exactly (same style as workflow path resolution)

### Details

Change 1: Update error message (line 47-48):
```python
# Before:
if target not in ("rag", "session", "workflow"):
    raise ValueError(
        f"target must be 'rag', 'session', or 'workflow', got: {target!r}"
    )

# After:
if target not in ("rag", "session", "workflow", "eventbus"):
    raise ValueError(
        f"target must be 'rag', 'session', 'workflow', or 'eventbus', got: {target!r}"
    )
```

Change 2: Add eventbus path resolution (after line 65):
```python
# After the existing if/elif chain:
if resolved == "rag":
    self._db_path = db_cfg.rag_db_path
elif resolved == "session":
    self._db_path = db_cfg.session_db_path
elif resolved == "workflow":
    self._db_path = db_cfg.workflow_db_path
elif resolved == "eventbus":  # NEW - one line addition
    self._db_path = db_cfg.eventbus_db_path
else:
    raise ValueError(f"unknown target: {resolved!r}")
```

Change 3: Update _default_load_vec logic (line 52):
```python
# Before:
self._default_load_vec = resolved == "rag"

# After - no change needed, already correct for eventbus (False)
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Type check | `uv run mypy scripts/db/helper.py` | No type errors |
| Lint | `uv run ruff check scripts/db/helper.py` | No lint errors |
| Manual verify | `python -c "from db.helper import SQLiteHelper; print(SQLiteHelper('eventbus').DB_PATH)"` | Output: `/opt/llm/db/eventbus.sqlite` |
| Manual verify vec | `python -c "from db.helper import SQLiteHelper; h = SQLiteHelper('eventbus'); print(h._default_load_vec)"` | Output: `False` (no vec extension for eventbus) |
