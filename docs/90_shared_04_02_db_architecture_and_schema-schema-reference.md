---
title: "DB Architecture and Schema - Schema Reference"
category: shared
tags:
  - shared
  - db
  - rag-sqlite
  - session-sqlite
  - workflow-sqlite
  - timestamp-policy
related:
  - 90_shared_00_document-guide.md
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
  - 90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md
source:
  - 90_shared_04_01_db_architecture_and_schema-overview-and-config.md
---

# DB Architecture and Schema

- Overview → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 5. `rag.sqlite` Schema

### `documents` table

| Column | Type | Constraint |
|---|---|---|
| `doc_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `url` | TEXT | UNIQUE NOT NULL |
| `title` | TEXT | |
| `lang` | TEXT | NOT NULL CHECK (`lang IN ('ja', 'en')`) |
| `fetched_at` | TEXT | NOT NULL DEFAULT `datetime('now')` |
| `etag` | TEXT | |
| `last_modified` | TEXT | |
| `chunking_strategy` | TEXT | NOT NULL DEFAULT `'text'` |

### `chunks` table

| Column | Type | Constraint |
|---|---|---|
| `chunk_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `doc_id` | INTEGER | FK → `documents(doc_id)` |
| `chunk_index` | INTEGER | NOT NULL |
| `content` | TEXT | NOT NULL |
| `normalized_content` | TEXT | (NULL for English/code) |
| `chunk_type`        | TEXT | NOT NULL DEFAULT `'text'` |
| `source_file`       | TEXT | NOT NULL DEFAULT `''` |

### `chunks_fts` (FTS5 virtual table)

```sql
CREATE VIRTUAL TABLE chunks_fts USING fts5(
    content,
    content       = 'chunks',
    content_rowid = 'chunk_id',
    tokenize      = 'unicode61'
)
```

**Auto-sync triggers:** These triggers maintain `chunks_fts` consistency automatically. Manual sync is NOT needed.

| Trigger | Event | Behavior |
|---|---|---|
| `chunks_ai` | AFTER INSERT ON chunks | Inserts new row into `chunks_fts` using `COALESCE(new.normalized_content, new.content)` |
| `chunks_au` | AFTER UPDATE ON chunks | Deletes old row, inserts new row in `chunks_fts` |
| `chunks_ad` | AFTER DELETE ON chunks | Deletes row from `chunks_fts` using `COALESCE(old.normalized_content, old.content)` |
| `chunks_vec_ad` | AFTER DELETE ON chunks | Deletes corresponding entry from `chunks_vec` where `chunk_id = old.chunk_id` |

> **Important:** Never manually synchronize `chunks_fts` after INSERT/UPDATE/DELETE — triggers handle this automatically.

### `chunks_vec` (sqlite-vec virtual table)

```sql
CREATE VIRTUAL TABLE chunks_vec USING vec0(
    chunk_id  INTEGER PRIMARY KEY,
    embedding float[DIMS]
)
-- DIMS replaced at runtime from embedding_dims config (default 384)
```

Stores float32 little-endian BLOB. `DIMS` is substituted dynamically at runtime from embedding_dims config (default 384).

---

## 6. `session.sqlite` Schema

### `sessions` table

| Column | Type | Constraint |
|---|---|---|
| `session_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `created_at` | TEXT | NOT NULL DEFAULT `datetime('now')` |
| `title` | TEXT | |

### `messages` table

| Column | Type | Constraint |
|---|---|---|
| `message_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `session_id` | INTEGER | FK → `sessions(session_id)` ON DELETE CASCADE |
| `role` | TEXT | NOT NULL |
| `content` | TEXT | NOT NULL |
| `tool_calls` | TEXT | (JSON string) |
| `tool_call_id` | TEXT | Tool call correlation ID (for tool role messages). Persisted/restored by `SessionMessageRepository`. NULL for non-tool messages. |
| `created_at` | TEXT | NOT NULL DEFAULT `datetime('now')` |

### `memories` table

| Column | Type | Constraint |
|---|---|---|
| `memory_id` | TEXT | PRIMARY KEY (UUID v4) |
| `memory_type` | TEXT | CHECK (`semantic` or `episodic`) |
| `source_type` | TEXT | NOT NULL DEFAULT `'conversation'` |
| `session_id` | INTEGER | (NULL allowed) |
| `turn_id` | TEXT | (NULL allowed) |
| `project` | TEXT | NOT NULL DEFAULT `''` |
| `repo` | TEXT | NOT NULL DEFAULT `''` |
| `branch` | TEXT | NOT NULL DEFAULT `''` |
| `content` | TEXT | NOT NULL |
| `summary` | TEXT | NOT NULL DEFAULT `''` |
| `tags` | TEXT | NOT NULL DEFAULT `'[]'` (JSON array) |
| `importance` | REAL | NOT NULL DEFAULT 0.5 |
| `pinned` | INTEGER | NOT NULL DEFAULT 0 |
| `created_at` | TEXT | NOT NULL (ISO-8601) |
| `updated_at` | TEXT | NOT NULL (ISO-8601) |

### `memories_fts` (FTS5 virtual table)

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    memory_id UNINDEXED,
    content,
    summary,
    tags
)
```

- `memory_id UNINDEXED` — column excluded from FTS index (used for filtering, not search)
- Used by `FtsRetriever.search()` for BM25 full-text search on `content`, `summary`, `tags`

### `memories_vec` (sqlite-vec virtual table)

- `memory_id TEXT PRIMARY KEY`, `embedding FLOAT[384]`
- Written only when `embed_enabled=True` and embedding generation succeeds
- Used by `VectorRetriever.knn_search()` for KNN search

### `memory_links` table

| Column | Type | Constraint |
|---|---|---|
| `src_id` | TEXT | NOT NULL; part of PRIMARY KEY |
| `dst_id` | TEXT | NOT NULL; part of PRIMARY KEY |
| PRIMARY KEY | (`src_id`, `dst_id`) | |

No foreign keys (uses `INSERT OR IGNORE` for idempotency).
Records near-duplicate memory pairs for deduplication.

### `session_diagnostics` table

| Column | Type | Constraint |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `session_id` | INTEGER | FK → `sessions(session_id)` ON DELETE CASCADE |
| `kind` | TEXT | NOT NULL |
| `content` | TEXT | NOT NULL |
| `workflow_id` | TEXT | (NULL allowed) |
| `task_id` | TEXT | (NULL allowed) |
| `created_at` | TEXT | NOT NULL DEFAULT `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |

Index: `idx_session_diagnostics_session ON session_diagnostics(session_id)`

---

## 7. `workflow.sqlite` Schema

Initialized by `create_workflow_schema()`. Used by `agent/workflow/state_store.py`.

### `tasks` table

| Column | Type | Note |
|---|---|---|
| `task_id` | TEXT PK | UUID4 |
| `session_id` | TEXT | |
| `workflow_id` | TEXT | UUID4 for this workflow run |
| `turn_number` | INTEGER | |
| `workflow_version` | TEXT | NOT NULL |
| `status` | TEXT | `pending`/`running`/`pending_approval`/`completed`/`failed`/`halted` |
| `idempotency_key` | TEXT UNIQUE | `session_id:turn_number` |
| `created_at` | TEXT | ISO-8601 UTC |
| `updated_at` | TEXT | ISO-8601 UTC |

### `approvals` table

| Column | Type | Note |
|---|---|---|
| `approval_id` | TEXT PK | UUID4 |
| `task_id` | TEXT NOT NULL | FK → `tasks(task_id)` ON DELETE CASCADE |
| `stage_id` | TEXT | |
| `status` | TEXT | `pending`/`approved`/`rejected` |
| `reason` | TEXT | |
| `created_at` | TEXT | ISO-8601 UTC |
| `resolved_at` | TEXT | |
| `workflow_id` | TEXT NOT NULL DEFAULT '' | |

### `attempts`, `processed_events`, `artifacts` tables

See `scripts/db/schema_sql.py` for full DDL. All use `CREATE TABLE IF NOT EXISTS`.

---

## 7a. Timestamp Format Policy

All SQLite schema DEFAULT timestamps use `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` for consistency.

Tables using this format:

- `session_diagnostics.created_at` (Z suffix)
- `documents.fetched_at`, `sessions.created_at`, `messages.created_at`, `memories.created_at`, `memories.updated_at` (Z suffix)
- Event Bus: `events.published_at` (Z suffix)

Python-side timestamp generation (for workflow tables without DEFAULT): `datetime.now(UTC).isoformat()` — produces ISO-8601 with `+00:00` suffix (e.g., `2024-01-01T00:00:00+00:00`).

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`
- `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`

## Keywords

rag.sqlite
session.sqlite
workflow.sqlite
schema
timestamp format policy
