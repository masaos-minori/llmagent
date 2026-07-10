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
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
  - 90_shared_05_db_api_and_operations-maintenance-and-rotation.md
  - 90_shared_05_db_api_and_operations-recovery-and-reference.md
source:
  - 90_shared_05_db_api_and_operations-module-boundaries-and-helper.md
---

# DB API and Operations

- Schema → [90_shared_04_db_architecture_and_schema-overview-and-config.md](90_shared_04_db_architecture_and_schema-overview-and-config.md)

## 3. Protocol Groups in `db/store.py`

All protocols are `@runtime_checkable` — `isinstance()` check works.

### Embedding helpers

```python
from db.store import get_embedding_dims, get_embedding_bytes, validate_embedding_blob

dims = get_embedding_dims()      # reads agent.toml::embedding_dims; default 384
nbytes = get_embedding_bytes()   # dims * 4 (float32)
validate_embedding_blob(blob)    # TypeError if not bytes; ValueError if wrong size
```

### `VectorStore` Protocol

```python
class VectorStore(Protocol):
    def vec_insert(self, chunk_id: int, embedding: bytes) -> None: ...
    def vec_search(self, embedding: bytes, k: int) -> list[tuple[int, float]]: ...
    def vec_delete(self, chunk_id: int) -> None: ...
    def vec_count(self) -> int: ...
```

- `vec_search` returns `(chunk_id, distance)` pairs
- `vec_delete`: no-op if not found

### `DocumentStore` Protocol

```python
class DocumentStore(Protocol):
    def doc_upsert(self, url, title, lang, etag, last_modified) -> int: ...
    def doc_get(self, url) -> dict | None: ...
    def doc_list(self, lang, limit) -> list[dict]: ...
    def doc_delete(self, url) -> bool: ...
    def chunk_insert(self, doc_id, index, content, normalized=None, chunk_type="", source_file="") -> int: ...
    def chunk_count(self) -> int: ...
```

- `doc_upsert`: SELECT then UPDATE/INSERT; returns `doc_id`
- `doc_get` returns `{doc_id, url, title, lang, fetched_at, etag, last_modified}` or `None`
- `doc_list` returns `{doc_id, url, title, lang, fetched_at}` sorted `fetched_at DESC`
- `doc_delete`: deletes document + cascades to chunks; returns `True` if found
- `chunk_insert` uses `chunk_index`, `chunk_type`, and `source_file` columns in `chunks` table

### `SessionStore` Protocol

```python
class SessionStore(Protocol):
    def session_create(self) -> int: ...
    def session_list(self, limit) -> list[dict]: ...
    def session_rename(self, session_id, title) -> None: ...
    def session_delete(self, session_id) -> None: ...
    def message_save(self, session_id, role, content, tool_calls, tool_call_id=None) -> None: ...
    def message_list(self, session_id) -> list[dict]: ...
```

- `session_list` returns `{session_id, created_at, title}` sorted `created_at DESC`
- `session_delete` cascades to messages (ON DELETE CASCADE)
- `message_list` returns `{role, content, tool_calls, tool_call_id}` in `message_id ASC` order
- `tool_calls` is `str | None` (JSON string)
- `tool_call_id` is `str | None`; always set for `tool` role messages, NULL for all other roles

---

## 4. SQLite Backend Implementations

| Class | Protocol | Constructor | Notes |
|---|---|---|---|
| `SQLiteVectorStore(db)` | `VectorStore` | `db: SQLiteHelper` | Validates embedding BLOB size in `vec_insert` |
| `SQLiteDocumentStore(db)` | `DocumentStore` | `db: SQLiteHelper` | `doc_upsert` does SELECT then UPDATE/INSERT |
| `SQLiteSessionStore(db)` | `SessionStore` | `db: SQLiteHelper` | Session list returned `created_at DESC` |
| `SQLiteMemoryDeleteStore(db)` | `MemoryDeleteStore` | `db: SQLiteHelper` | Atomic cross-table delete for `memories`/`memories_fts`/`memories_vec` |

### `SessionMessageRepository` vs `SQLiteSessionStore`

| Layer | Owned responsibilities |
|---|---|
| `SessionMessageRepository` (agent layer) | role validation (`user`/`assistant`/`tool`/`system`), strict_mode skip behavior, content=None normalization, tool_calls JSON encode/decode, session-dependent persistence |
| `SQLiteSessionStore` (db adapter layer) | schema-aligned INSERT/LIST operations, minimal validation only |

**Rule:** Validation and encoding logic must NOT be duplicated in `SQLiteSessionStore`. It is a thin DB adapter — no role validation, no content normalization, no JSON encoding. All such concerns belong to `SessionMessageRepository`.

See [05_agent_09_data-layer-session-db.md](05_agent_09_data-layer-session-db.md) for the agent-side responsibility boundary view.

### `MemoryDeleteStore` / `SQLiteMemoryDeleteStore`

```python
from db.store import MemoryDeleteStore, SQLiteMemoryDeleteStore, MemoryDeleteResult

store = SQLiteMemoryDeleteStore(db)
result: MemoryDeleteResult = store.delete_memories_before(older_than_days=30)
# result.deleted — count of deleted entries
```

- Atomically deletes from `memories`, `memories_fts`, `memories_vec`
- `maintenance.py::prune_old_memories()` delegates to this class
- `MemoryDeleteStore` is a Protocol (structural type) that exists to preserve the option of a non-SQLite backend in the future. Today, `SQLiteMemoryDeleteStore` is the sole implementation.

---



---

## 6. Memory-Related Tables and Operations (`MemoryStore`)

`MemoryStore` is defined in `agent/memory/store.py` (NOT `db/`). It uses `SQLiteHelper("session")`.

Key methods:

| Method | Description |
|---|---|
| `add(entry, embedding=None)` | Insert into `memories` + `memories_fts`; optionally `memories_vec` |
| `upsert(entry, embedding=None)` | `INSERT OR REPLACE` + sync FTS/vec |
| `delete(memory_id)` | Delete 1 entry; returns `True` if found |
| `search_by_type(type, limit)` | Filter by `memory_type`; ordered `importance DESC, pinned DESC` |
| `pin(memory_id)` / `unpin(memory_id)` | Toggle pinned flag |
| `clear_by_session(session_id)` | Delete all entries for session |
| `count_vec()` | Row count in `memories_vec`; returns `0` if vec0 not loaded |

`prune_old_memories(db, older_than_days)` in `maintenance.py` delegates to
`SQLiteMemoryDeleteStore` for cross-table deletion.

---

## Related Documents

- `90_shared_00_document-guide.md`
- `90_shared_05_db_api_and_operations-module-boundaries-and-helper.md`
- `90_shared_05_db_api_and_operations-maintenance-and-rotation.md`
- `90_shared_05_db_api_and_operations-recovery-and-reference.md`

## Keywords

protocol groups
db/store.py
SQLite backend implementations
MemoryStore
