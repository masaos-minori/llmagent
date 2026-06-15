# Implementation: DB / Deploy — Workflow Infrastructure Setup

## Goal

Add `workflow_db_path` to `DbConfig`, extend `SQLiteHelper` to support `target="workflow"`, create `db/workflow_schema.py` with the Metadata DB DDL, and update `deploy/init_db.sh` and `deploy/deploy.sh` to initialise `workflow.sqlite`.

## Scope

**In:**
- `scripts/db/config.py` — add `workflow_db_path: str` field and parent-dir validation
- `scripts/db/helper.py` — extend `target` to accept `"workflow"` and resolve its path
- `scripts/db/workflow_schema.py` — new file: DDL for `tasks`, `attempts`, `processed_events`, `artifacts`
- `deploy/init_db.sh` — add `workflow.sqlite` initialisation block
- `deploy/deploy.sh` — add `config/workflows/` copy and ensure `agent/workflow/` is covered by rsync

**Out:**
- Any change to existing table schemas in `rag.sqlite` or `session.sqlite`
- Changes to `scripts/db/models.py` or other db modules

## Assumptions

1. `workflow.sqlite` is stored at `/opt/llm/db/workflow.sqlite` (default); overridable via `common.toml` key `workflow_db_path`.
2. `DbConfig.__post_init__` already validates parent directory existence for `rag_db_path` and `session_db_path`; the same check must be applied to `workflow_db_path`.
3. `SQLiteHelper` with `target="workflow"` never loads the sqlite-vec extension (`_default_load_vec = False`).
4. `workflow_schema.py` is invoked as `python -m db.workflow_schema` (similar to `create_schema.py` pattern) and is idempotent (`CREATE TABLE IF NOT EXISTS`).
5. The `deploy.sh` already rsyncs all of `scripts/` so no extra rsync line is needed for `agent/workflow/`; only the `config/workflows/` directory copy is missing.

## Implementation

### Target files

1. `scripts/db/config.py`
2. `scripts/db/helper.py`
3. `scripts/db/workflow_schema.py` (new)
4. `deploy/init_db.sh`
5. `deploy/deploy.sh`

### Procedure

1. Edit `scripts/db/config.py` — add field and validation.
2. Edit `scripts/db/helper.py` — extend `target` allowlist and path resolution.
3. Create `scripts/db/workflow_schema.py` — 4-table DDL + `__main__` entry point.
4. Edit `deploy/init_db.sh` — append workflow.sqlite init block.
5. Edit `deploy/deploy.sh` — append `config/workflows/` copy.

### Method

#### `scripts/db/config.py`

Add to `DbConfig` dataclass after `session_db_path`:
```python
workflow_db_path: str = "/opt/llm/db/workflow.sqlite"
```

In `__post_init__`, extend the loop tuple:
```python
for label, path_str in (
    ("rag_db_path", self.rag_db_path),
    ("session_db_path", self.session_db_path),
    ("workflow_db_path", self.workflow_db_path),
):
```

In `build_db_config()`, add to `DbConfig(...)`:
```python
workflow_db_path=cfg.get("workflow_db_path", "/opt/llm/db/workflow.sqlite"),
```

#### `scripts/db/helper.py`

Change L29 allowlist check:
```python
if target not in ("rag", "session", "workflow"):
    raise ValueError(f"target must be 'rag', 'session', or 'workflow', got: {target!r}")
```

Change L40-42 path resolution to three-way branch:
```python
if target == "rag":
    self._db_path = db_cfg.rag_db_path
elif target == "session":
    self._db_path = db_cfg.session_db_path
else:
    self._db_path = db_cfg.workflow_db_path
```

Set `_default_load_vec`:
```python
self._default_load_vec = target == "rag"
```
(already correct — `target == "rag"` evaluates False for "workflow")

Update `_connect` key derivation:
```python
key = (
    "rag_db_path" if self._target == "rag"
    else "session_db_path" if self._target == "session"
    else "workflow_db_path"
)
```

#### `scripts/db/workflow_schema.py`

```python
#!/usr/bin/env python3
"""db/workflow_schema.py
DDL for the Metadata DB (workflow.sqlite).

Tables: tasks, attempts, processed_events, artifacts.
Run as: PYTHONPATH=scripts python -m db.workflow_schema
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

from db.config import build_db_config


_DDL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS tasks (
    task_id          TEXT PRIMARY KEY,
    session_id       TEXT NOT NULL,
    turn_number      INTEGER NOT NULL,
    workflow_version TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'pending',
    idempotency_key  TEXT UNIQUE NOT NULL,
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id  TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'running',
    started_at  TEXT NOT NULL,
    ended_at    TEXT,
    error_msg   TEXT
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id    TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    task_id     TEXT NOT NULL REFERENCES tasks(task_id) ON DELETE CASCADE,
    stage_id    TEXT NOT NULL,
    uri         TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
"""


def init_schema(db_path: str) -> None:
    """Create workflow tables if they do not exist."""
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(_DDL)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    cfg = build_db_config()
    Path(cfg.workflow_db_path).parent.mkdir(parents=True, exist_ok=True)
    init_schema(cfg.workflow_db_path)
    print(f"workflow schema initialised: {cfg.workflow_db_path}")
```

#### `deploy/init_db.sh`

After the existing rag.sqlite block, append:
```bash
echo "--- schema init: ${DEPLOY_DB}/workflow.sqlite ---"
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python -m db.workflow_schema)

echo "--- table check: workflow.sqlite ---"
sqlite3 "${DEPLOY_DB}/workflow.sqlite" ".tables"
# expected: artifacts  attempts  processed_events  tasks
```

#### `deploy/deploy.sh`

After the existing config copy block, append:
```bash
echo "--- config/workflows/ → ${DEPLOY_CONFIG}/workflows/ ---"
mkdir -p "${DEPLOY_CONFIG}/workflows"
cp -r "${REPO_ROOT}/config/workflows/." "${DEPLOY_CONFIG}/workflows/"
```

### Details

- `workflow_schema.py` uses `executescript` which auto-commits; the additional `conn.commit()` is a no-op but safe.
- `PRAGMA foreign_keys=ON` inside `executescript` takes effect immediately.
- `idempotency_key` carries a UNIQUE constraint to enforce at-most-once task creation.
- `workflow_version` enables forward compatibility checks when workflow definitions change.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Type check | `uv run mypy scripts/db/config.py scripts/db/helper.py scripts/db/workflow_schema.py` | 0 new errors |
| Schema init | `PYTHONPATH=scripts python -m db.workflow_schema` | exits 0, prints path |
| Table check | `sqlite3 /opt/llm/db/workflow.sqlite ".tables"` | 4 tables present |
| Unit tests | `uv run pytest tests/test_db_helper.py tests/test_config_loader.py -v` | all pass |
| Lint | `uv run ruff check scripts/db/ --fix && uv run ruff check scripts/db/` | 0 errors |
