# Implementation: agent/services/db_maintenance_service.py — DTO return types

## Goal

Replace `dict` and `object` return types in `DbMaintenanceService` with typed DTOs:
`DbStats`, `DbHealth`, `DbCheckpointResult`, `DbPurgeResult`, `DbRecoverResult`.
Remove `list_urls()` from the public API (it raises `NotImplementedError`).

## Scope

**Target file**: `scripts/agent/services/db_maintenance_service.py`

In scope:
- `stats()` → returns `DbStats`
- `health()` → returns `DbHealth`
- `checkpoint()` → returns `DbCheckpointResult`
- `purge()` → returns `DbPurgeResult`
- `recover()` → returns `DbRecoverResult`
- `list_urls()` → removed (was `raise NotImplementedError`)

Out of scope:
- `rebuild_fts()` and `vacuum()` (both return `None`; no change needed)
- DB layer (`db/maintenance.py`) — dict keys are read as-is

## Assumptions

1. DTOs are in `agent/services/models.py`:
   - `DbStats(docs, chunks, sessions, messages: int)`
   - `DbHealth(integrity_ok: bool, wal_pages: int, size_bytes: int)`
   - `DbCheckpointResult(mode: str, pages_written: int)`
   - `DbPurgeResult(sessions_removed: int)`
   - `DbRecoverResult(integrity_ok: bool, recovered: bool, detail: str)`
2. `db.helper.SQLiteHelper.health_check()` returns a `dict` with keys to be confirmed
   at implementation time (inspect `db/helper.py`).
3. `db.maintenance.checkpoint_wal()` returns a `dict` with WAL checkpoint stats.
4. `db.maintenance.purge_old_sessions()` returns a `dict` with purge stats.
5. `db.maintenance.recover_corruption()` returns an object; inspect `db/maintenance.py`
   to determine what fields are available.
6. `DbMaintenanceError(RuntimeError)` in `exceptions.py` is raised when DB operations fail.

## Implementation

### Target file

`scripts/agent/services/db_maintenance_service.py`

### Procedure

**Inspect DB layer at implementation time**:
```bash
grep -n "def health_check\|return {" scripts/db/helper.py | head -20
grep -n "def checkpoint_wal\|def purge_old_sessions\|def recover_corruption\|return {" scripts/db/maintenance.py | head -30
```
Confirm dict keys before writing DTO constructors.

**Update `stats()`**:
```python
from agent.services.models import DbStats

def stats(self) -> DbStats:
    with SQLiteHelper("rag").open(row_factory=True) as db:
        docs = db.fetchall("SELECT COUNT(*) AS n FROM documents")[0]["n"]
        chunks = db.fetchall("SELECT COUNT(*) AS n FROM chunks")[0]["n"]
    with SQLiteHelper("session").open(row_factory=True) as db:
        sessions = db.fetchall("SELECT COUNT(*) AS n FROM sessions")[0]["n"]
        messages = db.fetchall("SELECT COUNT(*) AS n FROM messages")[0]["n"]
    return DbStats(docs=docs, chunks=chunks, sessions=sessions, messages=messages)
```

**Update `health()`** — map dict keys to `DbHealth` fields (confirm at implementation time):
```python
from agent.services.models import DbHealth

def health(self) -> DbHealth:
    with SQLiteHelper("session").open() as db:
        raw = db.health_check()
    return DbHealth(
        integrity_ok=raw.get("integrity_ok", False),
        wal_pages=raw.get("wal_pages", 0),
        size_bytes=raw.get("size_bytes", 0),
    )
```

**Update `checkpoint()`**:
```python
from agent.services.models import DbCheckpointResult

def checkpoint(self, mode: str | None) -> DbCheckpointResult:
    with SQLiteHelper("session").open(write_mode=True) as db:
        raw = checkpoint_wal(db, mode)
    return DbCheckpointResult(
        mode=mode or "passive",
        pages_written=raw.get("pages_written", 0),
    )
```

**Update `purge()`**:
```python
from agent.services.models import DbPurgeResult

def purge(self, max_sessions: int | None, max_age_days: int | None) -> DbPurgeResult:
    cfg_kwargs: dict[str, int] = {}
    if max_sessions is not None:
        cfg_kwargs["max_sessions"] = max_sessions
    if max_age_days is not None:
        cfg_kwargs["max_age_days"] = max_age_days
    cfg = RetentionConfig(**cfg_kwargs) if cfg_kwargs else None
    with SQLiteHelper("session").open(write_mode=True) as db:
        raw = purge_old_sessions(db, cfg)
    return DbPurgeResult(sessions_removed=raw.get("sessions_removed", 0))
```

**Update `recover()`**:
```python
from agent.services.models import DbRecoverResult

def recover(self, backup_path: str | None) -> DbRecoverResult:
    raw = recover_corruption(backup_path)
    # Inspect raw type at implementation time; adapt to DbRecoverResult fields
    if isinstance(raw, dict):
        return DbRecoverResult(
            integrity_ok=raw.get("integrity_ok", False),
            recovered=raw.get("recovered", False),
            detail=str(raw.get("detail", "")),
        )
    return DbRecoverResult(integrity_ok=False, recovered=False, detail=str(raw))
```

**Remove `list_urls()`** entirely.

### Method

`Edit` tool. Update each method in sequence. Remove `list_urls()` with an Edit that deletes lines.

### Details

- Inspect actual dict keys returned by `health_check()`, `checkpoint_wal()`,
  `purge_old_sessions()`, and `recover_corruption()` before coding the constructors.
  The dict key names in the plan are approximations.
- `DbMaintenanceError` wraps unexpected exceptions from DB operations if needed.
- Call sites in `cmd_db.py` that access dict keys must be updated to DTO field access.

## Validation plan

```bash
uv run pytest tests/ -k "db_maintenance or db" -v
uv run ruff check scripts/agent/services/db_maintenance_service.py
uv run mypy scripts/agent/services/db_maintenance_service.py
```
