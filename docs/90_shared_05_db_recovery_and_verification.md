---
title: "DB API - RAG Consistency, Corruption Recovery, and Verification"
category: shared
tags:
  - db
  - api
  - consistency
  - corruption
  - recovery
  - error handling
  - verification
  - recreation
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_05_db_module_boundaries_and_sqlitehelper.md
  - 90_shared_05_db_store_protocols.md
  - 90_shared_05_db_maintenance_and_ops.md
source:
  - 90_shared_05_db_module_boundaries_and_sqlitehelper.md
---

# DB API - RAG Consistency, Corruption Recovery, and Verification

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- Schema → [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)

---

## 7b. RAG Consistency Checks (`db/rag_consistency.py`)

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

| Function | Signature | Description |
|---|---|---|
| `check_rag_consistency(db)` | `-> RagConsistencyReport` | Read-only: chunks/FTS/vec row counts + orphan detection |
| `is_consistent(report)` | `-> bool` | True if no orphans and FTS gap = 0 |
| `summarize_issues(report)` | `-> list[str]` | Human-readable issue descriptions |

### `RagConsistencyReport`

```python
@dataclass(frozen=True)
class RagConsistencyReport:
    chunks: int
    fts: int
    vec: int
    orphan_vec_count: int
    fts_gap: int              # chunks - fts; positive = missing FTS entries
    fts_orphan_count: int     # fts - chunks; positive = extra FTS entries (data loss risk)
```

**Usage:**

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues

report: RagConsistencyReport = check_rag_consistency(db)
if not is_consistent(report):
    for issue in summarize_issues(report):
        print(issue)
```

- `fts_gap > 0` → FTS trigger missed some inserts; fix: `/db rag rebuild-fts`
- `orphan_vec_count > 0` → vec trigger failed; fix: re-ingest affected URLs
- Read-only; does not repair inconsistencies.

**Recovery flow:**
1. `PRAGMA integrity_check` on `target` DB
2. `dry_run=True` → return result without modifying DB
3. Result `"ok"` → run VACUUM; return `action="vacuum"` (or `"vacuum_failed"`)
4. Result not `"ok"` → archive corrupt file as `{stem}_corrupt_{timestamp}{suffix}`; copy `backup_path`; return `action="restored"` (or `"no_backup"` / `"error"`)

**Rotate archive format:** `{stem}_{YYYYMMDD_HHMMSS}{suffix}` in `archive_dir`
(default: `agent.toml::sqlite_archive_dir` → `/opt/llm/db/archive`).
Uses SQLite online backup API to preserve WAL integrity.

---

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

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)
- [90_shared_05_db_store_protocols.md](90_shared_05_db_store_protocols.md)
- [90_shared_05_db_maintenance_and_ops.md](90_shared_05_db_maintenance_and_ops.md)
- [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)

## Keywords

consistency
corruption
recovery
error handling
verification
recreation
