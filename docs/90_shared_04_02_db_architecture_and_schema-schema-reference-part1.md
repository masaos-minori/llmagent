---
title: "DB Architecture and Schema - Schema Reference (Part 1)"
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
  - 90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md
---

# DB Architecture and Schema

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 5. `rag.sqlite` スキーマ

### `documents` table

| Column | Type | Constraint |
|---|---|---|
| `doc_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `url` | TEXT | UNIQUE NOT NULL |
| `title` | TEXT 
| `lang` | TEXT | NOT NULL CHECK (`lang IN ('ja', 'en')`) |
| `fetched_at` | TEXT | NOT NULL DEFAULT `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |
| `etag` | TEXT 
| `last_modified` | TEXT 
| `chunking_strategy` | TEXT | NOT NULL DEFAULT `'text'` |

**矛盾（要修正）:** 従来 `datetime('now')` と記載していたが、`db/schema_sql.py` の `_RAG_SCHEMA_TEMPLATE` では `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`（ISO-8601 UTC、`Z` サフィックス付き）が実装されている。他の全テーブルのタイムスタンプ列（`created_at`/`updated_at`等）も同一フォーマットで統一されている（Explicit in code）。

### `chunks` table

| Column | Type | Constraint |
|---|---|---|
| `chunk_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `doc_id` | INTEGER | NOT NULL, FK → `documents(doc_id)` ON DELETE CASCADE |
| `chunk_index` | INTEGER | NOT NULL |
| `content` | TEXT | NOT NULL |
| `normalized_content` | TEXT | (英語/コードの場合は NULL) |
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

**自動同期トリガー:** これらのトリガーは `chunks_fts` の整合性を自動的に維持する。手動での同期は不要である。

| Trigger | Event | Behavior |
|---|---|---|
| `chunks_ai` | AFTER INSERT ON chunks | `COALESCE(new.normalized_content, new.content)` を用いて `chunks_fts` に新しい行を挿入する |
| `chunks_au` | AFTER UPDATE ON chunks | 古い行を削除し、`chunks_fts` に新しい行を挿入する |
| `chunks_ad` | AFTER DELETE ON chunks | `COALESCE(old.normalized_content, old.content)` を用いて `chunks_fts` から行を削除する |
| `chunks_vec_ad` | AFTER DELETE ON chunks | `chunk_id = old.chunk_id` に該当する `chunks_vec` のエントリを削除する |

> **重要:** INSERT/UPDATE/DELETE の後に `chunks_fts` を手動で同期してはならない — トリガーが自動的に処理する。

### `chunks_vec` (sqlite-vec virtual table)

```sql
CREATE VIRTUAL TABLE chunks_vec USING vec0(
    chunk_id  INTEGER PRIMARY KEY,
    embedding float[DIMS]
)
-- DIMS replaced at runtime from embedding_dims config (default 384)
```

float32 のリトルエンディアン BLOB を格納する。`DIMS` は実行時に embedding_dims の設定値から動的に置換される (デフォルト 384)。

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`
- `90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
- `90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md`

## Keywords

rag.sqlite
session.sqlite
workflow.sqlite
schema
timestamp format policy
