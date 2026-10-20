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
  - db_01_architecture_and_schema-overview-and-config.md
  - agent_09_01_data-layer-session-db.md
---
# DB API and Operations

- Schema → [db_01_architecture_and_schema-overview-and-config.md](db_01_architecture_and_schema-overview-and-config.md)

## 3. `db/store.py` Protocol Groups

All protocols are `@runtime_checkable`. The embedding helpers (`get_embedding_dims`, `get_embedding_bytes`, `validate_embedding_blob`) are exported from `db.store`; the dimension is a fixed code-level constant (`scripts/db/store_protocols.py::QWEN3_EMBEDDING_DIMS`), not config-driven, and `validate_embedding_blob()` rejects non-bytes (`TypeError`) and wrong-size (`ValueError`) blobs.

`VectorStore` covers vector insert, KNN search (returning `(chunk_id, distance)` pairs), delete (no-op if absent) and count. `DocumentStore` covers document upsert/get/list/delete and chunk insert/count; deleting a document cascades to its chunks. The `chunk_insert` field set intentionally matches `RagIngester._insert_chunk()` in `scripts/rag/ingestion/ingester.py`, so callers must verify consistency with the ingester when adding or modifying chunk fields. `SQLiteDocumentStore` raises `RuntimeError` if the generated row ID cannot be obtained (a defensive check that is normally unreachable). Method signatures: `db/store_protocols.py`.

---

## 4. SQLite Backend Implementation

`SQLiteVectorStore` and `SQLiteDocumentStore` implement the protocols above on `SQLiteHelper`; `SQLiteVectorStore` validates the embedding `BLOB` size on insert. `SQLiteMemoryDeleteStore` implements `MemoryDeleteStore` and performs atomic cross-table deletion across `memories`/`memories_fts`/`memories_vec`; `maintenance.py::prune_old_memories()` delegates to it. `MemoryDeleteStore` is a `Protocol` that allows future non-SQLite backends; `SQLiteMemoryDeleteStore` is currently the only implementation.

---

## 5. Memory-Related Tables and Operations (`MemoryStore`)

`MemoryStore` is defined in `agent/memory/store.py` (NOT in `db/`) and uses `SQLiteHelper('session')`. `add()` inserts into `memories` and `memories_fts`; when an embedding is supplied it also inserts into `memories_vec` in the same transaction, and a failure of that insert (for example, `vec0` not loaded) raises and rolls the whole write back instead of storing the entry without its vector row. `upsert()` also syncs FTS and vec. `MemoryStore.count_vec()` and the module-level `count_vec()` in `agent/memory/count_ops.py` raise `sqlite3.OperationalError` when `memories_vec` is unavailable (for example, when `vec0` is not loaded). The `session` connection loads `vec0` by default (see the `load_vec` description in the DB overview). Cross-table deletion of old memories is delegated to `SQLiteMemoryDeleteStore`.

---

## Keywords

- shared
- db
- protocol-backend
