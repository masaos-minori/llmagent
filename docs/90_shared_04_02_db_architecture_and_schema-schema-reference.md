---
title: "DB Architecture and Schema"
area: shared
tags:
  - shared
  - db
  - schema
related:
---
# DB Architecture and Schema

- Overview → [90_shared_01_overview.md](90_shared_01_overview.md)
- DB API → [90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md](90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md)

## 5. rag.sqlite Schema

### `documents` table

Document metadata: doc_id (INTEGER PK AUTOINCREMENT), url (TEXT UNIQUE NOT NULL), title (TEXT nullable), lang (TEXT NOT NULL CHECK ja/en), fetched_at (TEXT NOT NULL — ISO-8601 UTC Z-suffix, always provided by callers), etag (TEXT nullable), last_modified (TEXT nullable), chunking_strategy (TEXT NOT NULL DEFAULT 'text'). Timestamp format corrected in db/schema_sql.py _RAG_SCHEMA_TEMPLATE to use strftime('%Y-%m-%dT%H:%M:%SZ', 'now') instead of datetime('now'); all other tables' timestamp columns (created_at/updated_at etc) unified under same format.

### `chunks` table

Chunk metadata: chunk_id (INTEGER PK AUTOINCREMENT), doc_id (INTEGER NOT NULL FK → documents(doc_id) ON DELETE CASCADE), chunk_index (INTEGER NOT NULL), content (TEXT NOT NULL), normalized_content (TEXT nullable for English/code), chunk_type (TEXT NOT NULL DEFAULT 'text'), source_file (TEXT NOT NULL DEFAULT '').

### `chunks_fts` (FTS5 virtual table)

FTS5 virtual table for full-text search on chunk content. Uses COALESCE(new.normalized_content, new.content) for insertion/update triggers. Automatic synchronization via AFTER INSERT/AFTER UPDATE/AFTER DELETE triggers on chunks table. IMPORTANT: Do not manually synchronize chunks_fts after INSERT/UPDATE/DELETE — triggers handle it automatically.

### `chunks_vec` (sqlite-vec virtual table)

sqlite-vec virtual table for vector similarity search. Stores float32 little-endian BLOB. chunk_id INTEGER PRIMARY KEY, embedding FLOAT[DIMS] where DIMS is `scripts/db/store_protocols.py::get_embedding_dims()`, a fixed code-level constant (not a config key).

---

## 6. session.sqlite Schema

Tables: sessions, messages, memories, memories_fts, memories_vec, memory_links, session_diagnostics. sessions stores session metadata (PK: session_id, created_at, title). messages stores conversation history (FK: session_id → sessions ON DELETE CASCADE; includes tool_calls/tool_call_id for tool-role messages). memories stores semantic/episodic memories (PK: memory_id UUID v4; fields: memory_type, source_type, session_id, turn_id, project/repo/branch, content, summary, tags, importance, pinned, created_at/updated_at). memories_fts is FTS5 virtual table for BM25 search on content/summary/tags (memory_id UNINDEXED). memories_vec is sqlite-vec virtual table for KNN retrieval on embedding[384] (written only when embed_enabled=True). memory_links is many-to-many deduplication table (src_id/dst_id as composite PK, no FK, uses INSERT OR IGNORE). session_diagnostics tracks system-level events separately from conversation messages (different lifecycle/query patterns; FK: session_id → sessions ON DELETE CASCADE).

---

## 7. workflow.sqlite Schema

Initialized by `create_workflow_schema()`, used by `agent/workflow/state_store.py`. Tables: tasks (PK: task_id UUID4; fields include session_id, workflow_id, turn_number, workflow_version, status, idempotency_key, created_at/updated_at), approvals (PK: approval_id UUID4; FK: task_id → tasks ON DELETE CASCADE; fields include stage_id, status, reason, created_at/resolved_at, workflow_id), attempts/processed_events/artifacts (DDL in `scripts/db/schema_sql.py`; all use CREATE TABLE IF NOT EXISTS), workflow_schema_version (append-only log: version(TEXT)/applied_at(TEXT); current version = max(applied_at); create_workflow_schema() inserts only when latest version differs from WORKFLOW_SCHEMA_VERSION constant — idempotent). Schema version mismatch: check_workflow_schema() (agent startup) and deploy/pre-flight both compare latest version against WORKFLOW_SCHEMA_VERSION constant, fail with [FATAL]/RuntimeError naming both versions if mismatch (includes case where no row exists yet). Recovery: re-run deploy/init_db.sh or call create_workflow_schema() directly.

---

## 8. eventbus.sqlite Schema

Independent persistence domain per [ADR-008](adr/ADR-008-sqlite-4db-separation.md) INV-04: `eventbus.sqlite` is the system of record for Event, Offset, Delivery, and DLQ state. Schema authority: `scripts/db/schema_sql.py::build_eventbus_schema_sql()` (bootstrap DDL) and `scripts/eventbus/db.py` (incremental migration at service startup — see [90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md](90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md) section 8b). Table/column detail: [06_eventbus_03_persistence_schema_and_replay.md](06_eventbus_03_persistence_schema_and_replay.md).

---

## 7a. Timestamp Format Policy

SQLite DEFAULT timestamps use strftime('%Y-%m-%dT%H:%M:%SZ', 'now') (Z suffix). Python-side timestamps (workflow tables without DEFAULT): datetime.now(UTC).isoformat() produces +00:00 suffix. Consistent across: session_diagnostics, documents, sessions, messages, memories, Event Bus events.
