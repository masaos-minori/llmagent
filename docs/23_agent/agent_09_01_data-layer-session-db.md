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
| `workflow.sqlite` | Workflow engine | Tasks, attempts, processed events, artifacts |

**Design judgment:** `session_diagnostics` is separated from `messages` — since diagnostic events are not visible to the LLM, they are managed separately from conversation history.

### Session Message Persistence

Session messages are persisted only through `SessionMessageRepository` over `SQLiteHelper`; it owns role validation, `strict_mode`, content normalization and `tool_calls` JSON encoding.

`replace_messages()` writes the compressed snapshot and updates the `/undo` compression boundary (`sessions.undo_floor_message_id`) in the same transaction, so the boundary and the snapshot never diverge. The boundary is a `messages` row ID, which keeps it valid after `/session load`.

### Session Retention Policy

`db/maintenance.py`'s `purge_old_sessions()` deletes old sessions based on `RetentionConfig`, following an age-based then count-based order. Deleting a session propagates to `messages` via `ON DELETE CASCADE`, but never to memory tables; memory retention is independent and is applied only by `/memory prune`. The purge runs only on demand (`/session purge`); no scheduler invokes it automatically. (Explicit in code — `scripts/agent/commands/cmd_session.py`, `scripts/agent/services/db_maintenance_service.py`)

### Memory Table Ownership

When `use_memory_layer=True`, the memory subsystem uses both JSONL and SQLite:

- SQLite `memories` (in `session.sqlite`) is the source of truth for current memory state; `memories_fts`, `memories_vec` and `memory_links` live in the same DB, and the FTS and vector tables are derived indexes.
- The JSONL file (`{memory_jsonl_dir}/memories.jsonl`) is an append-only archive for import/export and disaster recovery.

`memories.session_id` records the source session of a memory for provenance.
It does not establish ownership and intentionally has no foreign-key constraint
to `sessions`. The value is retained after the source session is deleted.

**Design judgment:** The SQLite memory tables are the source of truth for the current memory state. JSONL is maintained as an append-only archive for import/export and disaster recovery. Deletes and pin changes are recorded as change events in the JSONL archive and replayed by `/memory rebuild`; a delete or pin change with no change event in the archive is not reproduced.

### Role of `session_diagnostics`

- Stores diagnostic events (LLM transfer errors, guard hints, partial completions). It is separate from `messages` and is NOT referenced by `fetch_messages()`.
- `save()` unconditionally applies `_filter_sensitive_fields()` before insertion, independent of encryption: filtering stays active even when no encryption key is set.
- Rows can be encrypted with `encrypt=True`. `fetch()` decrypts with the configured Fernet key; a row that cannot be decrypted (for example after key rotation) is returned with its stored ciphertext in `content` and a warning is logged, never raised.
- `_purge_old_diagnostics()` applies `retention_days`.

**Design judgment:** Diagnostic rows are operator-facing auxiliary data, not conversation history. A failed decryption must not block reading the remaining rows, so the failure is reported only through the warning log. A caller that needs plaintext must treat a `content` value that starts with the Fernet token prefix as undecryptable. Rotating `encryption_key` makes older encrypted rows unreadable; keep the previous key until those rows pass `retention_days`.

## Responsibility Boundary

- **Canonical Source**: `agent/diagnostic_store.py`, `db/maintenance.py`
- **Schema**: `schema_sql.py` (authority for detailed schema definitions)

## Key Constraints

- Valid roles for the `messages` table: `user` / `assistant` / `tool` / `system`; `diagnostic` is **NOT** a valid role, so diagnostic events are persisted ONLY in `session_diagnostics`.
- JSONL is an append-only archive of memory lines and change events (delete, pin, unpin); existing lines are never rewritten.

## Known Limitations

None currently known.

## Keywords

- session.sqlite
- session_diagnostics
- SessionMessageRepository
- session retention
