---
title: "DB API and Operations - Recovery and Reference"
category: shared
tags:
  - shared
  - db
  - corruption-recovery
  - error-handling
  - verification
  - ai-reference
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_db_api_and_operations-protocol-and-backend.md
  - 90_shared_05_db_api_and_operations-maintenance-and-rotation.md
source:
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_db_architecture_and_schema-overview-and-config.md](90_shared_04_db_architecture_and_schema-overview-and-config.md)

## 9. Corruption Recovery

```python
from db.recovery import recover_corruption
from db.models import RecoveryResult

result = recover_corruption(
    backup_path="/opt/llm/db/backup/rag.sqlite",
    target="rag",
    dry_run=False,
)
```

### `RecoveryResult`

```python
@dataclass(frozen=True)
class RecoveryResult:
    success: bool
    action: str      # "vacuum" | "vacuum_failed" | "restored" | "no_backup" | "error"
    detail: str | None = None
    dry_run: bool = False
```

---

## 10. Error Handling

| Error | Behavior |
|---|---|
| `sqlite3.OperationalError` (busy/locked) | Auto-wait via `PRAGMA busy_timeout` (default 30s) |
| `sqlite3.IntegrityError` | Propagates to caller; does not occur in upsert paths |
| sqlite-vec load error | `sqlite3.OperationalError` → connection failure |
| Schema DDL failure | Exception re-raised from `executescript()` |
| Integrity check failure | Error logged + backup restore attempted |
| `prune_old_memories` failure | STRICT: exception propagates; BEST_EFFORT: returns `MaintenanceResult(success=False)` |
| `commit()` error | Logs WARNING + re-raises `sqlite3.OperationalError` |
| `close()` error | Logs WARNING; does NOT raise |

---

## 11. DB Recreation Procedure

Schema changes require DB recreation — no migration support exists.

**Step 1: Archive** — run `rotate_all_dbs()` to archive all three production DBs:

```bash
uv run python -c "from db.rotation import rotate_all_dbs; rotate_all_dbs()"
```

**Step 2: Delete** — manually remove the DB files:

```bash
rm /opt/llm/db/rag.sqlite /opt/llm/db/session.sqlite /opt/llm/db/workflow.sqlite
```

DB paths are resolved from `agent.toml` keys `rag_db_path`, `session_db_path`, `workflow_db_path`.

**Step 3: Recreate** — run `create_schema()` to initialize empty DBs:

```bash
uv run python -c "from db.create_schema import create_schema; create_schema()"
```

**Important notes:**
- Recreated DBs are empty — existing records are NOT migrated automatically.
- `create_schema()` also initializes `eventbus.sqlite` if not yet present.
- If only one DB needs recreation, use individual functions: `create_rag_schema()`, `create_session_schema()`, `create_workflow_schema()`.

---

## 12. Verification Plan

```bash
# Schema initialization
uv run pytest tests/test_create_schema.py

# DB maintenance
uv run pytest tests/test_db_maintenance.py

# Type check
uv run mypy scripts/db/

# Full integration: create DB → check all tables exist
python -c "from db.create_schema import create_schema; create_schema()"
sqlite3 /opt/llm/db/rag.sqlite ".tables"
sqlite3 /opt/llm/db/session.sqlite ".tables"
```

---

## 13. AI Reference Guide

| Question | Answer |
|---|---|
| How to open a DB connection | `with SQLiteHelper("rag").open(row_factory=True) as db:` |
| How to write atomically | `with db.begin_immediate():` inside an `open(write_mode=True)` context |
| What does `target="workflow"` connect to | `workflow.sqlite` — task tracking DB |
| How to validate embedding BLOB | `validate_embedding_blob(blob)` from `db.store` |
| How to purge old sessions | `purge_old_sessions(db, RetentionConfig(...))` — returns `MaintenanceResult`; check `.success` |
| How to recover from corruption | `recover_corruption(backup_path=..., target="rag")` |
| Does `prune_old_memories` catch exceptions? | **STRICT** (default): propagates; **BEST_EFFORT**: caught and returned in `MaintenanceResult` |
| How to use BEST_EFFORT mode | Pass `mode=MaintenanceMode.BEST_EFFORT` to `vacuum_db`, `purge_old_sessions`, or `prune_old_memories` |
| How to check RAG consistency | `check_rag_consistency(db)` → `is_consistent(report)` + `summarize_issues(report)` |

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_db_api_and_operations-protocol-and-backend.md`
- `90_shared_05_db_api_and_operations-maintenance-and-rotation.md`

## Keywords

corruption recovery
error handling
DB recreation procedure
verification plan
ai reference guide
