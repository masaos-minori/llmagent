# Implementation Plan: DB Config + Helper + Schema + Deploy (Step 1)

## Goal

Add `workflow.sqlite` support to the DB layer (config, helper, schema, deploy scripts) so that WorkflowEngine can connect to a dedicated metadata database with WAL mode and schema initialization.

## Scope

**In:**
- `scripts/db/config.py`: Add `workflow_db_path` field to `DbConfig` dataclass, validation, and builder
- `scripts/db/helper.py`: Add `"workflow"` as valid target, resolve workflow DB path
- `scripts/db/workflow_schema.py`: DDL for tasks / attempts / processed_events / artifacts tables
- `deploy/init_db.sh`: Add workflow.sqlite initialization step
- `deploy/deploy.sh`: Add rsync for `db/workflow_schema.py`

**Out:**
- Workflow engine logic (Step 6)
- Orchestrator integration (Step 7)
- Config file changes (Step 2, separate)

## Assumptions

1. `workflow.sqlite` is a standalone DB (not shared with rag/session).
2. WAL mode is enforced to avoid lock contention with other DBs.
3. The `workflow_version` TEXT field on `tasks` table tracks definition version mismatches.
4. `deploy.sh` uses rsync for scripts/ so new files are automatically included; explicit cp for db/*.py is needed only if deploy.sh changed from rsync to individual copies.

## Implementation

### Target Files

| File | Change Type |
|---|---|
| `scripts/db/config.py` | Modify |
| `scripts/db/helper.py` | Modify |
| `scripts/db/workflow_schema.py` | New |
| `deploy/init_db.sh` | Modify |
| `deploy/deploy.sh` | Modify (if needed) |

### Procedure

#### 1. Update `scripts/db/config.py`

Add `workflow_db_path: str = "/opt/llm/db/workflow.sqlite"` to `DbConfig`:

```python
@dataclass
class DbConfig:
    rag_db_path: str
    session_db_path: str
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"  # NEW
    sqlite_vec_so: str = ""
    sqlite_timeout: int = 30
    sqlite_busy_timeout_ms: int = 30000
    embedding_dims: int = 384

    def __post_init__(self) -> None:
        # ... existing validations ...
        for label, path_str in (
            ("rag_db_path", self.rag_db_path),
            ("session_db_path", self.session_db_path),
            ("workflow_db_path", self.workflow_db_path),  # NEW
        ):
            parent = Path(path_str).parent
            if not parent.exists():
                raise ValueError(f"{label} parent directory does not exist: {parent}")

def build_db_config() -> DbConfig:
    cfg = ConfigLoader().load_all()
    return DbConfig(
        rag_db_path=cfg.get("rag_db_path", ""),
        session_db_path=cfg.get("session_db_path", ""),
        workflow_db_path=cfg.get("workflow_db_path", "/opt/llm/db/workflow.sqlite"),  # NEW
        sqlite_vec_so=cfg.get("sqlite_vec_so", ""),
        sqlite_timeout=int(cfg.get("sqlite_timeout", 30)),
        sqlite_busy_timeout_ms=int(cfg.get("sqlite_busy_timeout_ms", 30000)),
        embedding_dims=int(cfg.get("embedding_dims", 384)),
    )
```

#### 2. Update `scripts/db/helper.py`

Add `"workflow"` to valid targets and path resolution:

```python
class SQLiteHelper:
    def __init__(self, target: str = "rag") -> None:
        if target not in ("rag", "session", "workflow"):  # MODIFIED
            raise ValueError(f"target must be 'rag', 'session', or 'workflow', got: {target!r}")
        self._target = target
        self._default_load_vec = target == "rag"
        # ...
        self._db_path = (
            db_cfg.rag_db_path if target == "rag"
            else db_cfg.session_db_path if target == "session"
            else db_cfg.workflow_db_path  # NEW
        )
```

Update `_connect()` method to handle workflow key:

```python
def _connect(self) -> sqlite3.Connection:
    key = {
        "rag": "rag_db_path",
        "session": "session_db_path",
        "workflow": "workflow_db_path",  # NEW
    }[self._target]
    if not self._db_path:
        raise ValueError(f"{key} is not configured in common.toml")
```

#### 3. Create `scripts/db/workflow_schema.py`

DDL for 4 tables with proper constraints and indexes:

```python
#!/usr/bin/env python3
"""workflow_schema.py — DDL for workflow.sqlite metadata database."""

import sqlite3
import sys
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    session_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    workflow_version TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'running', 'completed', 'failed', 'halted')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(session_id, turn_number)
);

CREATE TABLE IF NOT EXISTS attempts (
    attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    stage TEXT NOT NULL CHECK(stage IN ('plan', 'execute', 'verify', 'retry')),
    status TEXT NOT NULL CHECK(status IN ('running', 'completed', 'failed', 'timeout')),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    error_message TEXT,
    attempt_number INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS processed_events (
    event_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    stage_id TEXT NOT NULL,
    artifact_ref TEXT,
    processed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(task_id),
    stage_id TEXT NOT NULL,
    uri TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_attempts_task ON attempts(task_id);
CREATE INDEX IF NOT EXISTS idx_processed_events_task ON processed_events(task_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id);
"""

def init_workflow_db(db_path: str | None = None) -> sqlite3.Connection:
    """Initialize workflow.sqlite with schema and return connection."""
    if db_path is None:
        from db.config import build_db_config
        db_path = build_db_config().workflow_db_path

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn

if __name__ == "__main__":
    conn = init_workflow_db()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Initialized {db_path} with tables: {[t[0] for t in tables]}")
    conn.close()
```

#### 4. Update `deploy/init_db.sh`

Add workflow.sqlite initialization after rag.sqlite:

```bash
echo "--- スキーマ初期化: ${DEPLOY_DB}/workflow.sqlite ---"
(cd /opt/llm && PYTHONPATH="${DEPLOY_SCRIPTS}" uv run python "${DEPLOY_SCRIPTS}/db/workflow_schema.py")

echo "--- テーブル確認 ---"
sqlite3 "${DEPLOY_DB}/rag.sqlite" ".tables"
sqlite3 "${DEPLOY_DB}/workflow.sqlite" ".tables"
# 期待値: tasks  attempts  processed_events  artifacts
```

#### 5. Update `deploy/deploy.sh`

Since deploy.sh uses rsync for scripts/, the new `db/workflow_schema.py` is automatically included. No change needed unless deploy.sh switches to individual cp statements.

### Details

- Use `datetime('now')` default for timestamp columns (SQLite native, no Python dependency)
- `UNIQUE(session_id, turn_number)` on tasks prevents duplicate task records per turn
- `CHECK` constraints enforce status/phase enums at DB level
- Foreign keys enforced via `PRAGMA foreign_keys=ON` in SQLiteHelper.write_mode
- All table/index names use snake_case consistent with existing schema

## Validation Plan

| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/db/` | 0 errors |
| Type check | `uv run mypy scripts/db/` | no new errors |
| DB init | `PYTHONPATH=scripts python -m db.workflow_schema` | tables created |
| Schema verification | `sqlite3 workflow.sqlite ".tables"` | 4 tables + indexes |
| Existing tests | `uv run pytest tests/test_sqlite_helper.py -v` | all pass |
| Import layer | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
