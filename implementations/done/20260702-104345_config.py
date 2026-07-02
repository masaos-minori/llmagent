# Implementation: DbConfig - Add eventbus_db_path field

## Goal

Add `eventbus_db_path` as a first-class DB path managed by `DbConfig`.

## Scope

- DbConfig dataclass: add field, update __post_init__ validation, update build_db_config()

## Assumptions

1. Default value is "/opt/llm/db/eventbus.sqlite" matching existing convention
2. sqlite_timeout, sqlite_busy_timeout_ms, embedding_dims apply to all DBs (shared)
3. No special connection pragmas needed for eventbus beyond defaults

## Implementation

### Target file

- `scripts/db/config.py`

### Procedure

1. Add `eventbus_db_path: str = "/opt/llm/db/eventbus.sqlite"` field after `workflow_db_path`
2. Update `__post_init__` validation loop to include `eventbus_db_path`
3. Update `build_db_config()` to read `eventbus_db_path` from common.toml with default

### Method

- Follow existing pattern exactly (same style as workflow_db_path)

### Details

```python
# In DbConfig dataclass, add after workflow_db_path:
eventbus_db_path: str = "/opt/llm/db/eventbus.sqlite"

# In __post_init__, add to validation loop:
for label, path_str in (
    ("rag_db_path", self.rag_db_path),
    ("session_db_path", self.session_db_path),
    ("workflow_db_path", self.workflow_db_path),
    ("eventbus_db_path", self.eventbus_db_path),  # NEW
):

# In build_db_config(), add to DbConfig constructor:
eventbus_db_path=cfg.get("eventbus_db_path", "/opt/llm/db/eventbus.sqlite"),
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Type check | `uv run mypy scripts/db/config.py` | No type errors |
| Lint | `uv run ruff check scripts/db/config.py` | No lint errors |
| Import test | `python -c "from db.config import DbConfig, build_db_config; c = DbConfig(rag_db_path='/opt/llm/db/rag.sqlite', session_db_path='/opt/llm/db/session.sqlite'); print(c.eventbus_db_path)"` | Output: `/opt/llm/db/eventbus.sqlite` |
