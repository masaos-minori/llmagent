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
| `session.sqlite` | Agent layer | Sessions, messages, conversation state, session diagnostics, Episodic Memory |
| `rag.sqlite` | RAG layer | Documents, chunks, vectors |
| `mdq.sqlite` | MCP (mdq-mcp) | Indexing Markdown documents and context compression |
| `workflow.sqlite` | Workflow engine | Tasks, attempts, processed events, artifacts |

**Design judgment:** `session_diagnostics` is separated from `messages` — since diagnostic events are not visible to the LLM, they are managed separately from conversation history.

### Session Message Persistence

Session messages are persisted only through `SessionMessageRepository` over `SQLiteHelper`; it owns role validation, `strict_mode`, content normalization and `tool_calls` JSON encoding.

The message repository is (re)bound lazily to the `AgentSession` facade's current `session_id`. A `session_id` change — for example after `/session load` — invalidates the cached repository, so persistence never attributes writes to a superseded session. `session_persister.py` and `DiagnosticStore` read the session id on every call and need no rebind. Skipped-save counters always reflect the live repository instance.

`replace_messages()` writes the compressed snapshot and updates the `/undo` compression boundary (`sessions.undo_floor_message_id`) in the same transaction, so the boundary and the snapshot never diverge. The boundary is a `messages` row ID, which keeps it valid after `/session load`.

### Session Retention Policy

`db/maintenance.py`'s `purge_old_sessions()` deletes old sessions based on `RetentionConfig`, following an age-based then count-based order. Deleting a session propagates to `messages` via `ON DELETE CASCADE`, but never to Episodic Memory; Episodic Memory retention is independent and managed internally (configurable per event type and state-aware; the period values are undecided, SHARED-005). The purge runs only on demand (`/session purge`); no scheduler invokes it automatically. (Explicit in code — `scripts/agent/commands/cmd_session.py`, `scripts/agent/services/db_maintenance_service.py`)

Retention follows ADR-008 Decision Detail #23: sessions by `purge_old_sessions()`, diagnostics by the `retention_days` purge, Episodic Memory by configurable, state-aware retention per event type (period values undecided, SHARED-005).

### Episodic Memory Ownership

Episodic Memory is the Agent's only persistent long-term memory (ADR-008 Decision Detail #24):

- Episodic Memory events and relations are authoritative data in `session.sqlite`; the Episodic FTS and Vector indexes are derived data.
- No JSONL file exists for Agent memory, and Repository Context is not stored in the Session DB.
- Episodic Memory is recovered only from a verified SQLite backup.

Episodic table names and the provenance of each Episodic event are not defined here (SHARED-005).

### Backup and Recovery Scope

Episodic Memory is part of the Session DB backup and of full Session DB recovery: `/session recover` restores the whole database, and Episodic Memory returns with it. Repository Context is not restored from a backup; it is reloaded from the configured repository files.

A `session.sqlite` file that does not match the current schema is archived and recreated (ADR-008 Decision Detail #22): export conversations with `/session export` first; session history and Episodic Memory are not carried over. This destructive recreation is the final policy for Episodic Memory.

`/clear`, `/undo`, session deletion, and session purge give no user-level Episodic deletion semantics.

### Role of `session_diagnostics`

- Stores diagnostic events (LLM transfer errors, guard hints, partial completions). It is separate from `messages` and is NOT referenced by `fetch_messages()`.
- `save()` consumes the injected, validated `DiagnosticsConfig` snapshot and performs no `agent.toml` read per operation. It unconditionally applies `_filter_sensitive_fields()` before insertion, independent of encryption: filtering stays active even when no encryption key is set.
- Encryption is by policy, not a caller flag: a record is Fernet-encrypted when a key is configured, otherwise the redacted content is stored as plaintext and secret-checked. A `_filter_sensitive_fields()` error fails the write closed with `RuntimeError`; the original content is never persisted. `fetch()` classifies each row by its stored `storage_format` and never returns ciphertext as ordinary `content`: an `encrypted` row is decrypted when the key still validates, and a row that cannot be decrypted (for example after key rotation) is marked `decrypt_failed` with `content=None` and a warning is logged.
- `_purge_old_diagnostics()` applies `retention_days`.

**Design judgment:** Diagnostic rows are operator-facing auxiliary data, not conversation history. A failed decryption must not block reading the remaining rows, so `fetch()` reports the failure distinctly via `storage_format=decrypt_failed` with `content=None` rather than surfacing ciphertext. Rotating `encryption_key` makes older encrypted rows unreadable; keep the previous key until those rows pass `retention_days`.

**Accepted storage posture (decision, 2026-10-25):** The owner formally accepted Option B — plaintext-with-redaction — for `session_diagnostics` in production. Fernet encryption remains disabled in shipped configs (`encryption_key` empty by default); it is enabled only through deployed out-of-band config. Each row records its `storage_format`: `encrypted` (key configured, content Fernet-encrypted), `plaintext` (no key; redacted by the fail-closed filter), or `decrypt_failed` (an `encrypted` row whose key no longer validates, surfaced with `content=None`). The active defense layers are:

- Unconditional `_filter_sensitive_fields()` redaction in `save()`, independent of encryption.
- Fail-closed redaction: a `_filter_sensitive_fields()` error raises `RuntimeError` and refuses the write; the original content is never persisted.
- Fail-closed secret detection: when no encryption key is set and redaction succeeded, the shared detector `detects_secrets()` from `agent/secrets_masker.py` (the same pattern set the masker applies, see `agent_10_01_operations-and-observability-startup-and-health.md`) matches the redacted content and raises `RuntimeError` and refuses the write.
- Lazy purge of rows older than `retention_days` (30) on each `save()`; `retention_days` is validated at config load, and 0 or less disables the purge.

Residual risk: pattern detection is best-effort. If Option A (encryption enabled) is ever adopted, the Fernet key must be supplied only through deployed out-of-band config and must never be committed to the repository. Disposition of pre-existing plaintext rows: N/A — the production DB `/opt/llm/agent.db` currently contains no tables, so `session_diagnostics` has no stored rows; future rows expire via the 30-day lazy purge.

## Responsibility Boundary

- **Implementation**: `agent/diagnostic_store.py`, `db/maintenance.py`
- **Schema**: `schema_sql.py` (authority for detailed schema definitions)

## Key Constraints

- Valid roles for the `messages` table: `user` / `assistant` / `tool` / `system`; `diagnostic` is **NOT** a valid role, so diagnostic events are persisted ONLY in `session_diagnostics`.

## Known Limitations

None currently known.

## Keywords

- session.sqlite
- session_diagnostics
- SessionMessageRepository
- session retention
