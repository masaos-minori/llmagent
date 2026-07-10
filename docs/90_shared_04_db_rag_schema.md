---
title: "DB Architecture - rag.sqlite Schema"
category: shared
tags:
  - db
  - architecture
  - rag
  - schema
  - documents
  - chunks
  - chunks_fts
  - chunks_vec
  - fts5
  - sqlite-vec
  - trigger
related:
  - 90_shared_00_document-guide.md
  - 90_shared_01_overview.md
  - 90_shared_04_db_overview_and_config.md
source:
  - 90_shared_04_db_overview_and_config.md
---

# DB Architecture - rag.sqlite Schema

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

---

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

## Related Documents

- [90_shared_00_document-guide.md](90_shared_00_document-guide.md)
- [90_shared_01_overview.md](90_shared_01_overview.md)
- [90_shared_04_db_overview_and_config.md](90_shared_04_db_overview_and_config.md)
- [90_shared_04_session_workflow_schemas.md](90_shared_04_session_workflow_schemas.md)
- [90_shared_04_db_operational.md](90_shared_04_db_operational.md)
- [90_shared_05_db_module_boundaries_and_sqlitehelper.md](90_shared_05_db_module_boundaries_and_sqlitehelper.md)

## Keywords

db
architecture
rag
schema
documents
chunks
chunks_fts
chunks_vec
fts5
sqlite-vec
trigger
