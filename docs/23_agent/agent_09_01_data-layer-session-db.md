---
title: "Agent Data Layer - Session DB"
area: agent
tags:
  - agent
  - data-layer
  - session-sqlite
related:
  - agent_00_document-guide.md
  - agent_09_02_data-layer-access-patterns.md
  - agent_09_03_data-layer-indexing-boundaries.md
  - agent_04_01_state-and-persistence-state-model.md
---

# Agent Data Layer

- State and Persistence → [agent_04_01_state-and-persistence-state-model.md](agent_04_01_state-and-persistence-state-model.md)

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

### Session Message Persistence

Session messages are persisted only through `SessionMessageRepository` over `SQLiteHelper`; it owns role validation, `strict_mode`, content normalization and `tool_calls` JSON encoding.

### Session Retention Policy

`db/maintenance.py`'s `purge_old_sessions()` deletes old sessions based on `RetentionConfig`, following an age-based then count-based order. Deleting a session propagates to `messages` via `ON DELETE CASCADE`. The purge runs only on demand (`/session purge`); no scheduler invokes it automatically. (Explicit in code — `scripts/agent/commands/cmd_session.py`, `scripts/agent/services/db_maintenance_service.py`)

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
- Can be encrypted with `encrypt=True`. `fetch()` decrypts rows with the configured Fernet key. When a row cannot be decrypted (for example after the key was rotated or changed), `fetch()` logs a warning and returns the row with its stored ciphertext in `content`; it does not raise.

**Design judgment:** Diagnostic rows are operator-facing auxiliary data, not conversation history. A failed decryption must not block reading the remaining rows, so the row is returned as stored and the failure is reported only through the warning log. A caller that needs plaintext must treat a `content` value that starts with the Fernet token prefix as undecryptable. Rotating `encryption_key` makes older encrypted rows unreadable; keep the previous key until those rows pass `retention_days`.
- `_purge_old_diagnostics()` applies the retention policy (`retention_days`).

**Design judgment:** Sensitive field filtering is applied independently of encryption. Filtering remains active even if no encryption key is set.

## Responsibility Boundary

- **Canonical Source**: `agent/diagnostic_store.py`, `db/maintenance.py`
- **Schema**: `schema_sql.py` (authority for detailed schema definitions)

## Key Constraints

- Valid roles for the `messages` table: `user` / `assistant` / `tool` / `system` — `diagnostic` is **NOT** a valid role.
- Diagnostic events are persisted ONLY in the `session_diagnostics` table.
- JSONL is an append-only archive — deletions and state changes are NOT replayed.

## Known Limitations

None currently known.

## Keywords

- session.sqlite
- session_diagnostics
- SessionMessageRepository
- session retention
