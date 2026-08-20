---
title: "Agent State and Persistence - State Model (Part 1)"
category: agent
tags:
  - agent
  - state
  - persistence
  - agentcontext
  - session
related:
  - 05_agent_00_document-guide.md
  - 05_agent_04_02_state-and-persistence-history-compression.md
  - 05_agent_04_03_state-and-persistence-platform-databases.md
source:
  - 05_agent_04_01_state-and-persistence-state-model.md
---

# Agent State and Persistence

- Runtime Architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- Turn Flow → [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- Data Layer (Schema) → [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## Purpose

Documents the relationship between session persistence and conversation history in the database.

## Design Intent

### Session Persistence Design Intent

`AgentSession` manages `session.sqlite`. The session lifecycle is as follows:

```text
AgentREPL.run()
  → AgentSession.start()              — INSERT into sessions; get session_id
  → each turn: AgentSession.save()    — INSERT into messages
  → /session load <id>                — fetch_messages() → reconstruct ctx.conv.history
  → /session delete <id>              — DELETE sessions + messages (CASCADE)
```

### Message Saving Rules

`save(role, content)` only saves valid roles: `user`, `assistant`, `tool`, `system`. Invalid roles or missing `session_id` are logged as warnings and counted. If `strict_mode=True`, both conditions raise a `RuntimeError` instead of skipping.

`save_many(messages)` processes multiple messages in a single transaction. `replace_messages(messages)` writes a snapshot of compressed history back to the DB.

### DiagnosticStore Separation Design

Diagnostic data (LLM transport errors, guard hints, session runtime summaries) is persisted in the `session_diagnostics` table via `DiagnosticStore`. It is separate from the `messages` table. Regarding the partial completion model for persistence, refer to [05_agent_03 §Partial-Completion Model](05_agent_03_01_turn-processing-flow-overview.md).

**Current Implementation Behavior:** `DiagnosticStore` only writes to the `session_diagnostics` table. Diagnostic data is persisted only through `session_diagnostics`; dual persistence to `diagnostics.jsonl` is not performed.

### Session Title Generation Fallback Logic

In the first user turn, if session title generation fails, the following fallbacks apply:

| Failure case | Fallback title | Log |
|---|---|---|
| LLM HTTP/Request error | If length > 32: `first_input[:29] + "..."`, else `first_input` | WARNING |
| LLM returns empty or invalid response | Same as above | WARNING |
| `first_input` is empty | `"(New Session)"` | WARNING |
| `set_title()` DB write failure | Title is not persisted; error is logged | ERROR |

All failure cases are non-blocking, and the session continues normally. When a fallback occurs, an audit log entry is issued: `session_title_fallback session_id=<id> fallback=<title> reason=<error>`. `set_title_pending` is reset to `False` in a `finally` block regardless of the result.

## Responsibility Boundary

### Session Persistence

`AgentSession` manages the `sessions` and `messages` tables in `session.sqlite`. See [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md) for details.

### Relationship Between Conversation History and Database

```text
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- During a session, `history` is the source of truth.
- The database is a persistent backup.
- `/session load <id>` reconstructs `ctx.conv.history` from the database.
- `delete_last_turn()` deletes the last (up to 2) rows from the DB.
- `undo_last_turn()` deletes everything after the last `role='user'` message.

## Key Constraints

### Separation of State Scopes

Session scope and turn scope are clearly separated. Turn scope values are reset at the end of each turn, while session scope values are maintained throughout the REPL lifetime.

### Verified History Changes

All history changes must go through verified methods. Raw list operations are prohibited.

### Single Boundary for RepositoryGateway

All write operations must go through `RepositoryGateway`. Direct calls that bypass this assumption do not undergo authorization checks.

## Operational Notes

- `replace_history()` is used as defense-in-depth during session restoration. If corrupted/tampered DB rows introduce reserved ephemeral keys, those rows are sanitized or discarded.
- The authorization prompt for `RepositoryGateway` relies on the batch-level gate enforcement.

## Known Limitations

- While rare, session restoration via `replace_history()` allows for cases where corrupted/tampered DB rows might introduce reserved ephemeral keys.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_04_02_state-and-persistence-history-compression.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`
- `05_agent_04_01_state-and-persistence-state-model.md`

## Keywords

AgentContext state model
ConversationState
TurnState
WorkflowState
RuntimeStats
session persistence
