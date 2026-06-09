# Implementation: db_maintenance_service.py — Wrap DB ops behind a service

## Goal

Create `agent/services/db_maintenance_service.py` and slim down `cmd_db.py` so the command
layer no longer directly uses `SQLiteHelper` or `db.maintenance` functions.

## Scope

- `scripts/agent/services/db_maintenance_service.py`: new file with `DbMaintenanceService`.
- `scripts/agent/commands/cmd_db.py`: each `_db_*` method delegates to the service.

## Assumptions

1. `DbMaintenanceService` wraps all 9 operations from `cmd_db.py`.
2. `cmd_db.py` keeps `parse_flag_int/str` usage for arg parsing; removes SQLiteHelper direct usage.
3. Error handling (try/except with print) stays in `cmd_db.py` since it's display logic.

## Implementation

### Target files

- `scripts/agent/services/db_maintenance_service.py` (new)
- `scripts/agent/commands/cmd_db.py`

### Procedure

**db_maintenance_service.py — representative methods:**

```python
"""agent/services/db_maintenance_service.py
DbMaintenanceService — wraps rag/session DB maintenance operations.
"""
from __future__ import annotations
import sqlite3
from db.helper import SQLiteHelper
from db.maintenance import (
    RetentionConfig, checkpoint_wal, purge_old_sessions,
    recover_corruption, vacuum_db,
)


class DbMaintenanceService:
    def stats(self) -> dict:
        with SQLiteHelper("rag").open(row_factory=True) as db:
            docs = db.fetchall("SELECT COUNT(*) AS n FROM documents")[0]["n"]
            chunks = db.fetchall("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
        with SQLiteHelper("session").open(row_factory=True) as db:
            sessions = db.fetchall("SELECT COUNT(*) AS n FROM sessions")[0]["n"]
            messages = db.fetchall("SELECT COUNT(*) AS n FROM messages")[0]["n"]
        return {"docs": docs, "chunks": chunks, "sessions": sessions, "messages": messages}

    def rebuild_fts(self) -> None:
        with SQLiteHelper("rag").open(write_mode=True) as db:
            db.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
            db.commit()

    def health(self) -> dict:
        with SQLiteHelper("session").open() as db:
            return db.health_check()

    def checkpoint(self, mode: str | None) -> dict:
        with SQLiteHelper("session").open(write_mode=True) as db:
            return checkpoint_wal(db, mode)

    def vacuum(self) -> None:
        with SQLiteHelper("session").open(write_mode=True) as db:
            vacuum_db(db)

    def purge(self, max_sessions: int | None, max_age_days: int | None) -> dict:
        cfg_kwargs = {}
        if max_sessions is not None:
            cfg_kwargs["max_sessions"] = max_sessions
        if max_age_days is not None:
            cfg_kwargs["max_age_days"] = max_age_days
        cfg = RetentionConfig(**cfg_kwargs) if cfg_kwargs else None
        with SQLiteHelper("session").open(write_mode=True) as db:
            return purge_old_sessions(db, cfg)

    def recover(self, backup_path: str | None) -> object:
        return recover_corruption(backup_path)
```

**cmd_db.py — update each `_db_*` method:**

```python
# Instantiate once per command call (stateless service)
def _get_svc(self) -> DbMaintenanceService:
    from agent.services.db_maintenance_service import DbMaintenanceService  # noqa: PLC0415
    return DbMaintenanceService()
```

Each `_db_*` method then calls `self._get_svc().<method>()` and handles display + errors.
`SQLiteHelper` import in `cmd_db.py` is removed entirely.

### Method

Create service file with all operations; update `cmd_db.py` to import and delegate.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Service exists | `ls scripts/agent/services/db_maintenance_service.py` | present |
| No SQLiteHelper in cmd_db | `grep "SQLiteHelper" scripts/agent/commands/cmd_db.py` | 0 matches |
| Lint | `uv run ruff check scripts/agent/` | 0 errors |
| Tests | `uv run pytest tests/test_agent_cmd_db.py -q` | all pass |
