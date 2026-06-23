# DB Architecture and Schema

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_db_api_and_operations.md](90_shared_05_db_api_and_operations.md)

## 1. Purpose

Documents the `db/` layer structure, DB file organization, `DbConfig`, `SQLiteHelper`
connection behavior, WAL/FTS5/sqlite-vec configuration, all table schemas, and schema
initialization approach.

---

## 2. Overall DB Layer Structure

```
db/
├── helper.py          SQLiteHelper — connection lifecycle, PRAGMA, vec extension
├── create_schema.py   DDL creation (rag + session schemas; idempotent)
├── store_protocols.py Protocol definitions (MemoryDeleteStore, VectorStore, ...)
├── store_impl.py      SQLite implementations of store protocols
├── store.py           Re-export stub — public API surface for db.store imports
├── maintenance.py     WAL checkpoint, VACUUM, purge, rotate, recover
├── tool_results.py    ToolResultStore — full tool result storage
└── workflow_schema.py workflow.sqlite DDL initialization
```

Three DB files:

| DB | Default path | Tables |
|---|---|---|
| `rag.sqlite` | `common.toml::rag_db_path` | `documents`, `chunks`, `chunks_fts`, `chunks_vec` |
| `session.sqlite` | `common.toml::session_db_path` | `sessions`, `messages`, `notes`, `tool_results`, `memories`, `memories_fts`, `memories_vec`, `memory_links`, `session_diagnostics` |
| `workflow.sqlite` | `common.toml::workflow_db_path` | `tasks`, `attempts`, `processed_events`, `artifacts`, `approvals` |

**Why separate DB files?** RAG indexing and conversation state have different access patterns.
`rag.sqlite` is write-heavy during ingestion, read-heavy during queries.
`session.sqlite` is append-heavy during conversations. Separation avoids WAL contention.

---

## 3. `DbConfig` (`db/config.py`)

```python
@dataclass   # frozen=False (default)
class DbConfig:
    rag_db_path: str           # path to rag.sqlite
    session_db_path: str       # path to session.sqlite
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"  # path to workflow.sqlite
    sqlite_vec_so: str = ""    # path to vec0.so (empty = vec extension not needed)
    sqlite_timeout: int = 30   # sqlite3.connect() timeout (seconds, >= 1)
    sqlite_busy_timeout_ms: int = 30000   # PRAGMA busy_timeout (ms)
    embedding_dims: int = 384  # embedding vector dimension
```

- `__post_init__` validates that parent directories exist
- `embed_url` field does NOT exist in `DbConfig`
- Constructed by `build_db_config()` in `db/config.py`
- `common.toml` is loaded via `ConfigLoader().load_all()` (included at index 0 of `_BASE_CONFIG_FILES`) — see [90_shared_03](90_shared_03_runtime_and_execution.md) §2a Config Ownership for the full ownership table

---

## 4. DB File Structure and `SQLiteHelper`

`SQLiteHelper` manages connection lifecycle. Constructor resolves config at init time.

```python
SQLiteHelper(target: DbTarget | str = "rag")
# DbTarget.RAG, DbTarget.SESSION, DbTarget.WORKFLOW, or string literal
# "rag"      → rag.sqlite
# "session"  → session.sqlite
# "workflow" → workflow.sqlite  (documented in 07_ref-sqlite.md; not in 07_spec_db.md)
```

> **Note:** `"workflow"` target exists in `07_ref-sqlite.md` but is absent from `07_spec_db.md`.
> See [90_shared_90 DOCMISS-01](90_shared_90_inconsistencies_and_known_issues.md).

**Connection setup (every `open()` call):**
1. Load sqlite-vec extension from `_vec_so` (rag target only); then `enable_load_extension(False)`
2. `PRAGMA journal_mode=WAL`
3. `PRAGMA synchronous=NORMAL`
4. `PRAGMA busy_timeout=30000` (from `common.toml::sqlite_busy_timeout_ms`)
5. `PRAGMA foreign_keys=ON` (when `write_mode=True`)

sqlite-vec is loaded only for `target="rag"`. Session and workflow targets do not load vec.

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
| `chunking_strategy` | TEXT | NOT NULL DEFAULT `'text'` (added via `migrate_schema()`) |

### `chunks` table

| Column | Type | Constraint |
|---|---|---|
| `chunk_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `doc_id` | INTEGER | FK → `documents(doc_id)` |
| `chunk_index` | INTEGER | NOT NULL |
| `content` | TEXT | NOT NULL |
| `normalized_content` | TEXT | (NULL for English/code) |

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

Stores float32 little-endian BLOB. `DIMS` is substituted dynamically by `_build_rag_schema_sql(dims)`.

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
| `tool_call_id` | TEXT | UNUSED — column exists in schema but not referenced by any code |
| `created_at` | TEXT | NOT NULL DEFAULT `datetime('now')` |

### `notes` table

| Column | Type | Constraint |
|---|---|---|
| `note_id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `content` | TEXT | NOT NULL |
| `created_at` | TEXT | NOT NULL DEFAULT `datetime('now')` |

### `tool_results` table

| Column | Type | Constraint |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT |
| `session_id` | INTEGER | (NULL allowed) |
| `turn` | INTEGER | NOT NULL |
| `tool_name` | TEXT | NOT NULL |
| `args_masked` | TEXT | |
| `full_text` | TEXT | NOT NULL |
| `summary` | TEXT | |
| `is_error` | INTEGER | NOT NULL DEFAULT 0 |
| `created_at` | TEXT | NOT NULL DEFAULT `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` |

Index: `idx_tool_results_session ON tool_results(session_id)`

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

## 7. `workflow.sqlite` Schema (`db/workflow_schema.py`)

Initialized by `init_schema(path)`. Used by `agent/workflow/state_store.py`.

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

See `db/workflow_schema.py` for full DDL. All use `CREATE TABLE IF NOT EXISTS`.

> **Note:** `workflow.sqlite` is documented only in `07_ref-sqlite.md`, not in `07_spec_db.md`.
> See [90_shared_90 DOCMISS-01](90_shared_90_inconsistencies_and_known_issues.md).

---

## 8. Schema Generation and Migration Approach

```python
# Initialize all schemas
from db.create_schema import create_schema
create_schema()   # calls create_rag_schema() + create_session_schema()

# workflow schema
from db.workflow_schema import init_schema
init_schema("/opt/llm/db/workflow.sqlite")
```

- All DDL uses `IF NOT EXISTS` — idempotent; safe to run multiple times
- `migrate_schema(db_name)` applies incremental `ALTER TABLE ... ADD COLUMN` changes
  (suppresses `duplicate column name` errors; safe on existing DBs)
- `embedding_dims` is substituted dynamically in `_build_rag_schema_sql(dims)` and `_build_session_schema_sql(dims)`

---

## 9. Constraint List

| Constraint | Value |
|---|---|
| SQLite version | 3.35+ required |
| sqlite-vec path | `/opt/llm/sqlite-vec/vec0.so` (from `common.toml::sqlite_vec_so`) |
| WAL mode | All connections; `PRAGMA journal_mode=WAL` |
| busy_timeout | 30,000 ms default (`common.toml::sqlite_busy_timeout_ms`) |
| Embedding dimension | 384 default (`common.toml::embedding_dims`) |
| Float format | float32 little-endian BLOB |
| Single-node only | No distributed/replica support |
| `common.toml` loading | Included in `ConfigLoader().load_all()` at index 0 — see [90_shared_03](90_shared_03_runtime_and_execution.md) §2a Config Ownership for ownership table |

---

## 10. AI Reference Guide

| Question | Answer |
|---|---|
| Where is rag.sqlite schema? | This document §5 |
| Where is session.sqlite schema? | This document §6 |
| Does `SQLiteHelper` support workflow.sqlite? | Yes — `target="workflow"` (undocumented in spec, see §4) |
| How is embedding dimension set? | `common.toml::embedding_dims` (default 384) |
| What initializes schemas? | `create_schema()` + `init_schema()` — idempotent |
| Are DB triggers documented? | Partially — see [90_shared_90 UNDOC-03](90_shared_90_inconsistencies_and_known_issues.md) |

---

## 11. Scaling Limits and Migration Signals

The current RAG architecture uses single-node SQLite. This is appropriate for
team-scale deployments with moderate corpus sizes and infrequent concurrent writes.
The following signals indicate when re-evaluation may be warranted.

### Corpus size

- **`chunks` table > ~500K rows:** KNN scan time in `chunks_vec` grows linearly with corpus
  size; start monitoring `/rag search` latency at this scale.
  *(Needs confirmation: actual threshold depends on hardware and embedding dimensions.)*
- **DB file size > ~10 GB:** VACUUM time, backup duration, and WAL checkpoint latency all
  increase; `/db vacuum` may take minutes instead of seconds.
  *(Needs confirmation.)*

### Write concurrency

- Multiple simultaneous `RagIngester` processes writing to the same `rag.sqlite` serialize
  at the WAL layer. If ingestion throughput becomes a bottleneck, SQLite write serialization
  may be limiting.
- **Signal:** WAL file grows faster than checkpoint reduces it. Monitor with `/db health`.

### FTS5 search latency

- **Signal:** `/rag search` consistently takes > 500 ms. FTS5 BM25 scales with document
  count; very large corpora may see degraded search speed.
  *(Needs confirmation.)*

### Operational complexity signals

- Backup and point-in-time recovery become complex as file size grows
- Multiple environments sharing the same DB file is not supported (SQLite is single-file)
- `/db consistency` issues become harder to repair at scale

### Migration signal checklist

When two or more of the following apply, consider an architecture review:

- [ ] KNN search latency > 1 s at p95
- [ ] DB file size > 20 GB
- [ ] WAL checkpoint consistently takes > 30 s
- [ ] Ingest queue depth consistently > 10 K unprocessed chunk files
- [ ] Multiple teams or processes need simultaneous write access

Use `/db health` and `/db consistency` to monitor these signals in normal operations.

### What to evaluate when limits approach

- **Vector search:** Dedicated vector databases (approximate nearest neighbor, distributed
  index) outperform `sqlite-vec` at > 1 M vectors
- **Full-text search:** Inverted-index search services handle large corpora with lower latency
- **Hybrid stores:** Relational DB + vector extension (e.g. `pgvector`-compatible) preserves
  SQL semantics while scaling write concurrency

> **Note:** All numeric thresholds above are planning estimates, not benchmarked guarantees.
> Actual limits depend on hardware, embedding dimensions, query patterns, and corpus
> characteristics. Validate with your specific deployment before treating any threshold as firm.
