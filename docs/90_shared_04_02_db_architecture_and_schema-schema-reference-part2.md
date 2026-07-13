---
title: "DB Architecture and Schema - Schema Reference (Part 2)"
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

## 6. `session.sqlite` スキーマ

### `sessions` table

| Column | Type | Constraint |
|---|---|---|
| `session_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `created_at` | TEXT | NOT NULL DEFAULT `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |
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
| `created_at` | TEXT | NOT NULL DEFAULT `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |

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

### `workflow_schema_version` table

| Column | Type | Note |
|---|---|---|
| `version` | TEXT NOT NULL | e.g. `1.0.0` |
| `applied_at` | TEXT NOT NULL | ISO-8601 UTC, `DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))` |

Append-only log — one row per version ever applied. The "current version" is the row with the maximum `applied_at`. `create_workflow_schema()` inserts a new row only when the latest recorded version differs from `WORKFLOW_SCHEMA_VERSION` (in `scripts/db/schema_sql.py`), keeping repeated runs idempotent.

### Schema version mismatch

Both `agent/repl_health.py::check_workflow_schema()` (agent startup) and `deploy/setup_services.sh`'s pre-flight block (deploy-time) compare the latest `workflow_schema_version.version` row against the `WORKFLOW_SCHEMA_VERSION` constant, and fail with a `[FATAL]`/`RuntimeError` message naming both the expected and found versions if they differ (including when no row exists yet — e.g. a `workflow.sqlite` created before this table existed).

**Recovery**: re-run `deploy/init_db.sh` (or call `create_workflow_schema()` directly) to bring the schema up to the expected version. `_WORKFLOW_MIGRATIONS` and the version-recording insert are both idempotent, so re-running is always safe.

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
- `90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md`

## Keywords

rag.sqlite
session.sqlite
workflow.sqlite
schema
timestamp format policy
