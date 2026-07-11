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

- 概要 → [90_shared_01_01_overview-purpose-and-scope.md](90_shared_01_01_overview-purpose-and-scope.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 5. `rag.sqlite` スキーマ

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

## 6. `session.sqlite` スキーマ

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
| `tool_call_id` | TEXT | ツール呼び出しの関連付け ID (tool ロールのメッセージ用)。`SessionMessageRepository` により永続化/復元される。tool 以外のメッセージでは NULL。 |
| `created_at` | TEXT | NOT NULL DEFAULT `datetime('now')` |

### `memories` table

| Column | Type | Constraint |
|---|---|---|
| `memory_id` | TEXT | PRIMARY KEY (UUID v4) |
| `memory_type` | TEXT | CHECK (`semantic` or `episodic`) |
| `source_type` | TEXT | NOT NULL DEFAULT `'conversation'` |
| `session_id` | INTEGER | (NULL 許容) |
| `turn_id` | TEXT | (NULL 許容) |
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

- `memory_id UNINDEXED` — FTS インデックスから除外されたカラム (検索用ではなくフィルタ用)
- `FtsRetriever.search()` により `content`、`summary`、`tags` に対する BM25 全文検索で使用される

### `memories_vec` (sqlite-vec virtual table)

- `memory_id TEXT PRIMARY KEY`、`embedding FLOAT[384]`
- `embed_enabled=True` かつ embedding 生成が成功した場合にのみ書き込まれる
- `VectorRetriever.knn_search()` による KNN 検索で使用される

### `memory_links` table

| Column | Type | Constraint |
|---|---|---|
| `src_id` | TEXT | NOT NULL; part of PRIMARY KEY |
| `dst_id` | TEXT | NOT NULL; part of PRIMARY KEY |
| PRIMARY KEY | (`src_id`, `dst_id`) | |

外部キーは持たない (冪等性のために `INSERT OR IGNORE` を使用)。
重複除去のため、ほぼ重複するメモリのペアを記録する。

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

インデックス: `idx_session_diagnostics_session ON session_diagnostics(session_id)`

---

## 7. `workflow.sqlite` スキーマ

`create_workflow_schema()` により初期化される。`agent/workflow/state_store.py` で使用される。

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

### `attempts`、`processed_events`、`artifacts` テーブル

完全な DDL は `scripts/db/schema_sql.py` を参照。すべて `CREATE TABLE IF NOT EXISTS` を使用する。

---

## 7a. タイムスタンプ形式ポリシー

すべての SQLite スキーマの DEFAULT タイムスタンプは、一貫性のため `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` を使用する。

この形式を使用するテーブル:

- `session_diagnostics.created_at` (Z サフィックス)
- `documents.fetched_at`、`sessions.created_at`、`messages.created_at`、`memories.created_at`、`memories.updated_at` (Z サフィックス)
- Event Bus: `events.published_at` (Z サフィックス)

Python 側でのタイムスタンプ生成 (DEFAULT を持たない workflow テーブル用): `datetime.now(UTC).isoformat()` — `+00:00` サフィックス付きの ISO-8601 を生成する (例: `2024-01-01T00:00:00+00:00`)。

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
