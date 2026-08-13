---
title: "DB API and Operations - Protocol and Backend"
category: shared
tags:
  - shared
  - db
  - protocol-groups
  - sqlite-backend
  - memory-store
related:
  - 90_shared_00_document-guide.md
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md
  - 90_shared_05_04_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- スキーマ → [90_shared_04_01_db_architecture_and_schema-overview-and-config.md](90_shared_04_01_db_architecture_and_schema-overview-and-config.md)

## 3. `db/store.py` のプロトコルグループ

All protocols are @runtime_checkable so isinstance() checks work. Embedding helpers: from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob; dims = get_embedding_dims() (reads agent.toml::embedding_dims, default 384); nbytes = get_embedding_bytes() (dims * 4 for float32); validate_embedding_blob(blob) (TypeError if not bytes, ValueError if wrong size). VectorStore(Protocol): vec_insert(chunk_id:int, embedding:bytes) → None, vec_search(embedding:bytes, k:int) → list[tuple[int,float]] (returns (chunk_id, distance) pairs), vec_delete(chunk_id:int) → None (no-op if not found), vec_count() → int. DocumentStore(Protocol): doc_upsert(url,title,lang,etag,last_modified) → int (SELECT then UPDATE/INSERT, returns doc_id), doc_get(url) → dict|None (returns {doc_id,url,title,lang,fetched_at,etag,last_modified} or None), doc_list(lang,limit) → list[dict] (returns {doc_id,url,title,lang,fetched_at} sorted by fetched_at DESC), doc_delete(url) → bool (deletes document and cascades to chunks, True if found), chunk_insert(doc_id,index,content,normalized=None,chunk_type='',source_file='') → int (uses chunks table columns chunk_index/chunk_type/source_file; field config intentionally matches scripts/rag/ingestion/ingester.py RagIngester._insert_chunk() INSERT per db/store_protocols.py docstring — caller must verify consistency with ingester when adding/modifying fields), chunk_count() → int. doc_upsert/chunk_insert (SQLiteDocumentStore) and session_create (SQLiteSessionStore) raise RuntimeError if RETURNING doc_id / INSERT lastrowid cannot be obtained (defensive check normally unreachable). SessionStore(Protocol): session_create() → int, session_list(limit) → list[dict] (returns {session_id,created_at,title} sorted by created_at DESC), session_rename(session_id,title) → None, session_delete(session_id) → None (cascades to messages via ON DELETE CASCADE), message_save(session_id,role,content,tool_calls,tool_call_id=None) → None, message_list(session_id) → list[dict] (returns {role,content,tool_calls,tool_call_id} ordered by message_id ASC; tool_calls is str|None JSON string; tool_call_id is str|None always set on tool-role messages, NULL on others).

---

## 4. SQLite バックエンド実装

SQLiteVectorStore(db: SQLiteHelper) implements VectorStore protocol; validates embedding BLOB size in vec_insert. SQLiteDocumentStore(db: SQLiteHelper) implements DocumentStore protocol; doc_upsert does SELECT then UPDATE/INSERT. SQLiteSessionStore(db: SQLiteHelper) implements SessionStore protocol; session list returned by created_at DESC. SQLiteMemoryDeleteStore(db: SQLiteHelper) implements MemoryDeleteStore protocol; atomic cross-table deletion across memories/memories_fts/memories_vec. SessionMessageRepository (agent layer) vs SQLiteSessionStore (db adapter layer): SessionMessageRepository handles role validation (user/assistant/tool/system), strict_mode skip behavior, content=None normalization, tool_calls JSON encode/decode, session-dependent persistence. SQLiteSessionStore performs only schema-consistent INSERT/LIST operations with minimal validation. Rule: do NOT duplicate validation/encoding logic in SQLiteSessionStore — it is a thin DB adapter that performs no role validation, content normalization, or JSON encoding. These concerns belong entirely to SessionMessageRepository. For agent-side responsibility boundary view see 05_agent_09_01_data-layer-session-db.md. MemoryDeleteStore/SQliteMemoryDeleteStore: from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult; store = SQLiteMemoryDeleteStore(db); result = store.delete_memories_before(older_than_days=30); result.deleted is count of deleted entries. Atomic deletion from memories/memories_fts/memories_vec. maintenance.py::prune_old_memories() delegates to this class. MemoryDeleteStore is a Protocol (structural type) existing to leave room for future non-SQLite backends; currently SQLiteMemoryDeleteStore is the only implementation.

---

---

**注意: セクション5は未作成。** 隣接ファイルのセクション番号（90_shared_05_01: 1-2, 90_shared_05_03: 7-7b, 90_shared_05_04: 9-13）から、セクション5の範囲は空欄となっている。

## 6. メモリ関連テーブルと操作 (`MemoryStore`)

MemoryStore is defined in agent/memory/store.py (NOT db/). Uses SQLiteHelper('session'). Main methods: add(entry, embedding=None) inserts into memories+memories_fts; optionally also into memories_vec as needed. upsert(entry, embedding=None) does INSERT OR REPLACE + syncs FTS/vec. delete(memory_id) deletes one entry; returns True if found. search_by_type(type, limit) filters by memory_type; order importance DESC, pinned DESC. pin(memory_id)/unpin(memory_id) toggles pinned flag. clear_by_session(session_id) deletes all entries linked to session. count_vec() returns row count of memories_vec; returns 0 if vec0 not loaded. maintenance.py prune_old_memories(db, older_than_days) delegates cross-table deletion to SQLiteMemoryDeleteStore.

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_01_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_03_db_api_and_operations-maintenance-and-rotation.md`
- `90_shared_05_04_db_api_and_operations-recovery-and-reference.md`
