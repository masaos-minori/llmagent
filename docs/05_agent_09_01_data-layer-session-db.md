---
title: "Agent Data Layer - Session DB"
area: agent
tags:
  - agent
  - data-layer
  - session-sqlite
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_09_01_data-layer-session-db.md
---

# Agent Data Layer

- State and Persistence → [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

## Purpose

Documents the responsibility scope of the Session DB, data ownership boundaries, and responsibility boundaries with the RAG layer.

## Design Intent

### Database Responsibility Separation

| Database | Owner | Responsibility |
|---|---|---|
| `session.sqlite` | Agent layer | Sessions, messages, memory, diagnostics |
| `rag.sqlite` | RAG layer | Documents, chunks, vectors |
| `mdq.sqlite` | MCP (mdq-mcp) | Indexing Markdown documents and context compression |
| `workflow.sqlite` | Workflow engine | Tasks, attempts, processed events, approvals, artifacts |

**Design judgment:** `session_diagnostics` is separated from `messages` — since diagnostic events are not visible to the LLM, they are managed separately from conversation history.

### SessionMessageRepository vs SQLiteSessionStore Responsibility Separation

What `SessionMessageRepository` handles:
- Role validation (`user` / `assistant` / `tool` / `system`)
- `strict_mode` behavior (raises `RuntimeError` on skip)
- Avoiding saving when a session does not exist
- Normalization of `content=None`
- JSON encoding/decoding of `tool_calls`

What `SQLiteSessionStore` handles:
- Simple DB INSERT/LIST operations
- Persistence compliant with schema
- Minimal validation only

**Design judgment:** Validation and encoding logic must NOT be duplicated in `SQLiteSessionStore`. It is a thin DB adapter and performs no role validation, content normalization, or JSON encoding; these concerns belong entirely to `SessionMessageRepository`.

### Session Retention Policy

`db/maintenance.py`'s `purge_old_sessions()` deletes old sessions based on `RetentionConfig`, following an age-based then count-based order. Deleting a session propagates to `messages` via `ON DELETE CASCADE`.

### Memory Table Ownership

When `use_memory_layer=True`, the memory subsystem uses both JSONL and SQLite:

| Storage | Path | Contents |
|---|---|---|
| JSONL | `{memory_jsonl_dir}/memories.jsonl` | Append-only archive for import/export and disaster recovery |
| SQLite: `memories` | `session.sqlite` | The source of truth for current memory state |
| SQLite: `memories_fts` | Same DB | FTS5 index for memory content |
| SQLite: `memory_links` | Same DB | Many-to-many links between memories |
| SQLite: `memories_vec` | Same DB | KNN embeddings for any vector search |

**Design judgment:** The SQLite memory tables are the source of truth for the current memory state. JSONL is maintained as an append-only archive for import/export and disaster recovery. Deletions and changes to pin/unpin status are NOT replayed from JSONL.

### Role of `session_diagnostics`

- Stores diagnostic events (LLM transfer errors, guard hints, partial completions).
- Separated from the `messages` table and is NOT referenced by `fetch_messages()`.
- `save()` unconditionally applies `_filter_sensitive_fields()` before insertion to filter sensitive fields.
- Can be encrypted with `encrypt=True`; `fetch()` decrypts rows using the configured Fernet key, falling back to raw content if decryption fails.
- `_purge_old_diagnostics()` applies the retention policy (default 30 days).

**Design judgment:** Sensitive field filtering is applied independently of encryption. Filtering remains active even if no encryption key is set.

## Responsibility Boundary

- **Canonical Source**: `shared/tool_executor.py`, `agent/diagnostic_store.py`, `db/maintenance.py`
- **Schema**: `schema_sql.py` (authority for detailed schema definitions)

## Key Constraints

- Valid roles for the `messages` table: `user` / `assistant` / `tool` / `system` — `diagnostic` is **NOT** a valid role.
- Diagnostic events are persisted ONLY in the `session_diagnostics` table.
- Do NOT duplicate validation and encoding logic in `SQLiteSessionStore`.
- JSONL is an append-only archive — deletions and state changes are NOT replayed.

## Operational Notes

- Unknown

## Known Limitations

- Encrypted rows in `session_diagnostics` are not decrypted during `fetch()`.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_09_02_data-layer-access-patterns.md`
- `05_agent_09_03_data-layer-indexing-boundaries.md`

## Keywords

session.sqlite
session_diagnostics
SessionMessageRepository
SQLiteSessionStore
session retention
