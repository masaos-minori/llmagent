---
title: "DB Architecture - session.sqlite and workflow.sqlite Schemas"
category: shared
tags:
  - db
  - architecture
  - session
  - workflow
  - schema
  - sessions
  - messages
  - memories
  - memories_fts
  - memories_vec
  - memory_links
  - session_diagnostics
  - tasks
  - attempts
  - processed_events
  - artifacts
  - approvals
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_04_db_overview_and_config.md
  - 90_shared_04_db_rag_schema.md
source:
  - 90_shared_04_db_overview_and_config.md
---

# DB Architecture - session.sqlite and workflow.sqlite Schemas

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

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

### `attempts`, `processed_events`, `artifacts` tables

See `scripts/db/schema_sql.py` for full DDL. All use `CREATE TABLE IF NOT EXISTS`.

---

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)
- [90_shared_04_db_rag_schema.md](90_shared_04_db_rag_schema.md)
- [90_shared_04_db_operational.md](90_shared_04_db_operational.md)
- [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

## Keywords

db
architecture
session
workflow
schema
sessions
messages
memories
memories_fts
memories_vec
memory_links
session_diagnostics
tasks
attempts
processed_events
artifacts
approvals
