---
title: "Agent State and Persistence - State Model and Session Persistence"
area: agent
tags:
  - agent
  - state
  - persistence
  - agentcontext
  - session
related:
  - agent_00_document-guide.md
  - agent_04_02_state-and-persistence-history-compression.md
  - agent_04_03_state-and-persistence-platform-databases.md
  - agent_02_runtime-architecture.md
  - agent_03_01_turn-processing-flow-overview.md
  - agent_09_01_data-layer-session-db.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
---

# Agent State and Persistence

- Runtime Architecture → [agent_02_runtime-architecture.md](agent_02_runtime-architecture.md)
- Turn Flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
- Data Layer (Schema) → [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md)

## Purpose

Documents the relationship between session persistence and conversation history in the database.

## Design Intent

### Session Persistence Design Intent

`AgentSession` manages the session and message tables in `session.sqlite`. A session row is created at REPL start, each turn's messages are appended, `/session load <id>` reconstructs `ctx.conv.history` from stored messages, and `/session delete <id>` removes the session together with its messages (cascade).

`session_id` is mutable on restore: `/session load` (`restore_session()`) reassigns the live session's `session_id`, and the message repository rebuilds to the new id on next use, so post-restore turns are attributed to the restored session. Skipped-save counters belong to the live repository instance.

### Message Saving Rules

`save(role, content)` only saves valid roles: `user`, `assistant`, `tool`, `system`. Invalid roles or missing `session_id` are logged as warnings and counted. If `strict_mode=True`, both conditions raise a `RuntimeError` instead of skipping.

`save_many(messages)` processes multiple messages in a single transaction. `replace_messages(messages)` writes a snapshot of compressed history back to the DB.

### DiagnosticStore Separation Design

Diagnostic data (LLM transport errors, guard hints, session runtime summaries) is persisted in the `session_diagnostics` table via `DiagnosticStore`. It is separate from the `messages` table. Regarding the partial completion model for persistence, refer to [agent_03 Partial-Completion Model](agent_03_03_turn-processing-flow-workflow-engine.md).

**Current Implementation Behavior:** `DiagnosticStore` writes only to the `session_diagnostics` table, which is the sole persistence for diagnostic data.

### Session Title Generation Fallback Logic

In the first user turn, if session title generation fails, the following fallbacks apply:

| Failure case | Fallback title | Log |
|---|---|---|
| LLM request error, or empty/invalid response | `first_input`, truncated with `"..."` when over the title length limit | WARNING |
| `first_input` is empty | `"(New Session)"` | WARNING |
| `set_title()` DB write failure | Title is not persisted | ERROR |

All failure cases are non-blocking, and the session continues normally. When a fallback occurs, an audit log entry is issued: `session_title_fallback session_id=<id> fallback=<title> reason=<error>`. `set_title_pending` is reset to `False` in a `finally` block regardless of the result.

## Responsibility Boundary

### Session Persistence

`AgentSession` owns the `sessions` and `messages` tables (see Design Intent). Schema details: [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md).

### Relationship Between Conversation History and Database

```text
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- During a session, `history` is the source of truth.
- The database is a persistent backup.
- `session load <id>` subcommand reconstructs `ctx.conv.history` from the database.
- `undo_last_turn()` deletes everything from the last `role='user'` message after the compression boundary; messages at or before the boundary are never deleted. The DB deletion succeeds before the in-memory history is changed.

### Session and Memory Responsibility Boundary

A session is responsible for restoring a conversation. Long-term memory is
responsible for reusing knowledge across sessions.

- `sessions` and `messages` preserve conversation history for `/session load`.
- `memories`, `memories_fts`, `memories_vec`, and `memory_links` preserve
  reusable knowledge extracted from conversations.
- Deleting or purging a session deletes its conversation history but does not
  delete memories extracted from that session.
- `memories.session_id` is provenance metadata, not an ownership relationship.
  It may refer to a session that has already been deleted and has no foreign-key
  constraint to `sessions`.
- `/undo`, history compression, `/session load`, `/session delete`, and
  `/session purge` do not modify long-term memory.
- Long-term memory is modified only by memory ingestion and `/memory` operations.
- `/session export` exports conversation history only. Memory backup and
  recovery use the JSONL archive and `/memory rebuild`.

Lifetimes differ: `ctx.conv.history` is session-scoped and is restored from `messages`. The memory injection message is a temporary system context for one turn; it is never persisted to `messages`, is not restored by `/session load`, and is removed when the turn ends. Deduplication between restored history and injected memory belongs to memory injection, which skips memories whose provenance `session_id` equals the current session; the session side has no deduplication duty.

## Key Constraints

### Separation of State Scopes

Session scope and turn scope are clearly separated. Turn scope values are reset at the end of each turn, while session scope values are maintained throughout the REPL lifetime.

### Verified History Changes

All history changes must go through verified methods. Raw list operations are prohibited.

### Single Boundary for RepositoryGateway

All write operations must go through `RepositoryGateway`. Direct calls that bypass this assumption do not undergo authorization checks.

## Operational Notes

- `replace_history()` is used as defense-in-depth during session restoration: rows that carry reserved ephemeral keys (corrupted or tampered DB rows) are sanitized or discarded.
- The authorization prompt for `RepositoryGateway` relies on the batch-level gate enforcement.

## Known Limitations

- Rare corrupted or tampered DB rows can introduce reserved ephemeral keys during session restoration; `replace_history()` sanitizes or discards them (see Operational Notes).

## Keywords

- AgentContext state model
- ConversationState
- TurnState
- WorkflowState
- RuntimeStats
- session persistence
