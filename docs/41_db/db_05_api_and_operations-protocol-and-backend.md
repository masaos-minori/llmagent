---
title: "DB API and Operations — Protocol and Backend"
area: shared
tags:
  - shared
  - db
  - protocol-backend
related:
  - db_04_api_and_operations-module-boundaries-and-helper.md
  - db_06_api_and_operations-maintenance-and-rotation.md
---
# DB API and Operations

- Schema → [db_01_architecture_and_schema-overview-and-config.md](db_01_architecture_and_schema-overview-and-config.md)

## 3. `db/store.py` Protocol Groups

All protocols are `@runtime_checkable`, so `isinstance()` checks work. Embedding helpers: `from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob`; `dims = get_embedding_dims()` (returns a fixed code-level constant, `scripts/db/store_protocols.py::QWEN3_EMBEDDING_DIMS`, not config-driven); `nbytes = get_embedding_bytes()` (dims * 4 for float32); `validate_embedding_blob(blob)` (raises `TypeError` if not bytes, `ValueError` if wrong size). 

`VectorStore(Protocol)`: `vec_insert(chunk_id:int, embedding:bytes) \rightarrow None`, `vec_search(embedding:bytes, k:int) \rightarrow list[tuple[int,float]]` (returns `(chunk_id, distance)` pairs), `vec_delete(chunk_id:int) \rightarrow None` (no-op if not found), `vec_count() \rightarrow int`. 

`DocumentStore(Protocol)`: `doc_upsert(url,title,lang,etag,last_modified) \rightarrow int` (performs `SELECT` then `UPDATE`/`INSERT`, returns `doc_id`), `doc_get(url) \rightarrow dict|None` (returns `{doc_id,url,title,lang,fetched_at,etag,last_modified}` or `None`), `doc_list(lang,limit) \rightarrow list[dict]` (returns `{doc_id,url,title,lang,fetched_at}` sorted by `fetched_at DESC`), `doc_delete(url) \rightarrow bool` (deletes document and cascades to chunks, `True` if found), `chunk_insert(doc_id,index,content,normalized=None,chunk_type='',source_file='') \rightarrow int` (uses `chunks` table columns `chunk_index`/`chunk_type`/`source_file`; field configuration intentionally matches `scripts/rag/ingestion/ingester.py`'s `RagIngester._insert_chunk()` `INSERT` as documented in `db/store_protocols.py` — callers must verify consistency with the ingester when adding/modifying fields), `chunk_count() \rightarrow int`. `doc_upsert`/`chunk_insert` (`SQLiteDocumentStore`) and `session_create` (`SQLiteSessionStore`) raise `RuntimeError` if `RETURNING doc_id` / `INSERT lastrowid` cannot be obtained (a defensive check that is normally unreachable). 

`SessionStore(Protocol)`: `session_create() \rightarrow int`, `session_list(limit) \rightarrow list[dict]` (returns `{session_id,created_at,title}` sorted by `created_at DESC`), `session_rename(session_id,title) \rightarrow None`, `session_delete(session_id) \rightarrow None` (cascades to messages via `ON DELETE CASCADE`), `message_save(session_id,role,content,tool_calls,tool_call_id=None) \rightarrow None`, `message_list(session_id) \rightarrow list[MessageRow]` (all messages of the session in insertion order)

---

## 4. SQLite Backend Implementation

`SQLiteVectorStore(db: SQLiteHelper)` implements the `VectorStore` protocol; validates embedding `BLOB` size in `vec_insert`. `SQLiteDocumentStore(db: SQLiteHelper)` implements the `DocumentStore` protocol; `doc_upsert` performs a `SELECT` followed by an `UPDATE`/`INSERT`. `SQLiteSessionStore(db: SQLiteHelper)` implements the `SessionStore` protocol; session lists are returned ordered by `created_at DESC`. Its usage status is described in [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md). `SQLiteMemoryDeleteStore(db: SQLiteHelper)` implements the `MemoryDeleteStore` protocol; provides atomic cross-table deletion across `memories`/`memories_fts`/`memories_vec`. 

The responsibility boundary between `SessionMessageRepository` (agent layer) and `SQLiteSessionStore` (db adapter layer) is defined in [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md); validation, normalization and JSON encoding must not be duplicated in the db adapter.

`MemoryDeleteStore`/`SQLiteMemoryDeleteStore`: `from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult`; `store = SQLiteMemoryDeleteStore(db)`; `result = store.delete_memories_before(older_than_days=30)`; `result.deleted` is the count of deleted entries. Performs atomic deletion from `memories`/`memories_fts`/`memories_vec`. `maintenance.py::prune_old_memories()` delegates to this class. `MemoryDeleteStore` is a `Protocol` (structural type) existing to allow for future non-SQLite backends; currently, `SQLiteMemoryDeleteStore` is the only implementation.

---

## 5. Memory-Related Tables and Operations (`MemoryStore`)

`MemoryStore` is defined in `agent/memory/store.py` (NOT in `db/`). It uses `SQLiteHelper('session')`. Main methods: `add(entry, embedding=None)` inserts into `memories` + `memories_fts`; optionally also into `memories_vec` as needed. `upsert(entry, embedding=None)` performs `INSERT OR REPLACE` + syncs `FTS`/`vec`. `delete(memory_id)` deletes a single entry; returns `True` if found. `search_by_type(type, limit)` filters by `memory_type`; orders by `importance DESC`, `pinned DESC`. `pin(memory_id)`/`unpin(memory_id)` toggles the `pinned` flag. `clear_by_session(session_id)` deletes all entries linked to a session. `count_vec()` returns the row count of `memories_vec`; returns `0` if `vec0` is not loaded. `maintenance.py prune_old_memories(db, older_than_days)` delegates cross-table deletion to `SQLiteMemoryDeleteStore`.

---

## Keywords

- shared
- db
- protocol-backend
