---
title: "Memory Layer — Module Reference"
category: agent
tags:
  - agent
  - agent
  - memory
  - semantic
  - episodic
  - embedding
related:
  - 05_agent_00_document-guide.md
---

# Memory Layer — Module Reference

## Module Reference

### 13. `services.py` — MemoryServices facade

Class `MemoryServices(injection, ingestion, store, retriever, embedding_client=None, *, use_memory_layer=False)`:

| Attribute / Method | Description |
|---|---|
| `injection` | MemoryInjectionService instance |
| `ingestion` | MemoryIngestionService instance |
| `store` | MemoryStore instance |
| `retriever` | HybridRetriever instance |
| `embedding_client` | EmbeddingClient (from retriever if not provided) |
| `get_activation_mode()` | Returns: "disabled" / "fts-only" / "degraded" / "hybrid" |
| `get_stats()` | Returns `dict` with keys: total (int), semantic (int), episodic (int), by_source (dict[str, int]), embed_skip (int), last_retrieval_mode (str), fts_fallback_count (int) |
| `on_session_start(session_id)` | Delegates to `injection.on_session_start()` |
| `on_session_stop(session_id, history, turn_id)` | Delegates to `ingestion.on_session_stop()` |
| `on_user_prompt(query, session_id)` | Delegates to `injection.on_user_prompt()` |



### 14. `mapper.py` — Row conversion utils

| Function | Returns | Description |
|---|---|---|
| `row_to_entry(dict)` | `MemoryEntry` | SQLite row to MemoryEntry |

Internal helper functions for float-to-BLOB conversion, timestamp stamping, and ISO 8601 timestamp generation.



### 15. `write_ops.py` — Write operations

| Function | Returns | Description |
|---|---|---|
| `add(entry, embedding=None, embed_dim=None)` | `None` | Insert + FTS sync; BEGIN IMMEDIATE for atomicity. When `embedding` is provided, also writes to memories_vec. |
| `upsert(entry, embedding=None, embed_dim=None)` | `None` | Insert-or-replace + FTS sync. When `embedding` is provided, also upserts memories_vec. |
| `delete(memory_id)` | `bool` | Remove entry by ID |
| `clear_by_session(session_id)` | `int` | Bulk delete for one session |



### 16. `pin_ops.py` — Pin/unpin operations

| Function | Returns | Description |
|---|---|---|
| `pin(memory_id, conn=None)` | `bool` | Set pinned=1; returns True when found. When `conn` is provided, uses that connection (caller must commit). |
| `unpin(memory_id, conn=None)` | `bool` | Set pinned=0; returns True when found. When `conn` is provided, uses that connection (caller must commit). |

## Related Documents

- `agent`
- `memory`
- `semantic`

## Keywords

agent
memory
semantic
episodic
embedding
