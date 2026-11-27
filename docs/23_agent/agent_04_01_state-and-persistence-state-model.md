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

`AgentSession` manages the session and message tables in `session.sqlite`. A session row is created at REPL start, each turn's messages are appended, `/session load <id>` reconstructs `ctx.conv.history` from stored messages, and `/session delete <id>` removes the session together with its messages (cascade). `/session load` keeps the conversation summary of a compressed session: one canonical summary row, recognized by a shared constant, is restored after the current prompt, while every other persisted system row is still dropped.

`session_id` is mutable on restore: `/session load` reassigns the live session's `session_id` as part of its transition commit, and the message repository rebuilds to the new id on next use, so post-restore turns are attributed to the restored session. Skipped-save counters belong to the live repository instance.

#### Session generation and target

The live session carries a monotonically increasing generation. It is runtime-only state (no schema column) that advances on every session id change, including a reload of the same id. An immutable session target pairs the session id with the generation. Work that must land in the session that started it, such as title generation, carries the target captured when it was created and is refused when the live session id or generation no longer matches, so a late result cannot change the current session. Title-generation pending state is tracked per session id, so a title task of an earlier session cannot flip it for the current one. Background tasks are registered with their type, instance, session id, and generation, and their failures are grouped by type.

#### Transition and persistence snapshots

A session transition (`/session load` and `/clear new`, see [agent_07_07](agent_07_07_cli-and-commands-slash-commands-session-mcp.md) for the command semantics) works from an immutable snapshot of the live session fields: id, generation, history, undo boundary, correlation id, and statistics. The new state is built off to the side, all fields are committed together, and the snapshot is restored when any step fails. Shutdown persistence takes one immutable snapshot (session id, generation, a copy of the history, turn id, and statistics) and uses it for both Memory extraction and diagnostics; persistence is refused when the generation changed since the capture. Memory extraction creates new entries on every run, so a session whose history was already finalized is not extracted again from an unchanged history.

### Message Saving Rules

`save(role, content)` only saves valid roles: `user`, `assistant`, `tool`, `system`. Invalid roles or missing `session_id` are logged as warnings and counted. If `strict_mode=True`, both conditions raise a `RuntimeError` instead of skipping.

`save_many(messages)` processes multiple messages in a single transaction. `replace_messages(messages)` writes a snapshot of compressed history back to the DB.

### Turn Persistence Boundary

A single turn-persistence boundary makes one agent turn's session-DB persistence all-or-nothing. One boundary is materialized per turn and owns every `messages` write for that turn: each turn-path writer routes its writes through the boundary instead of writing the repository directly, so a whole turn commits atomically or not at all.

On any persistence failure inside the turn, the boundary compensates and surfaces a distinct error:

- **Compensation.** On an append-only turn, only the turn's own rows are removed — those with a `message_id` greater than the turn-start marker, where the marker is the highest `message_id` present when the turn begins. Rows at or below the marker, including the marker row and every prior turn, are retained. On a turn that also compressed its history, the compression rewrite had replaced the session's rows, so compensation instead restores the captured turn-start rows — with their original `message_id` and `created_at`, at or below the marker — and resets the `/undo` boundary, rather than deleting above the marker; this returns the persisted session to its turn-start content instead of leaving it empty. The in-memory `ctx.conv.history` is restored element-wise to the snapshot captured at turn start, and `ctx.conv.undo_floor` to its turn-start value. If the restore itself fails, the rows are left as they are, the failure is logged, and the persistence error is still raised — compensation never falls back to deleting above the marker.
- **Compensation status.** The outcome of compensation is reported as a status: `completed` for a clean rollback, `failed` when the compensation itself raised, and `not_needed` when no write had committed. The status is carried on the persistence error and on the turn result, so the caller can distinguish a clean rollback from a failed compensation.
- **Dedicated error type.** A database failure inside the turn is raised as the dedicated conversation-persistence error type (wrapping the underlying database error), never a raw database error. It propagates from the boundary through the orchestrator, which records a distinct persistence error kind, to the REPL, which surfaces a dedicated "turn not persisted, history rolled back" message rather than the generic error format. The public error string carries the message plus the masked exception type name only; raw database detail stays on the wrapped cause for internal logs.

A session whose compensation failed is marked degraded. While it stays degraded the next turn is refused at the turn entry, and the REPL reports the refusal instead of dispatching a turn; a session transition starts a fresh, non-degraded session because it advances the generation. The criteria that clear the state are not defined yet — clearing is a separate follow-up work item.

This boundary is a failure-triggered path, distinct from the manual `/undo` command and from the save rules above; it does not change their semantics. Rows retained by compensation remain subject to `/undo` and history compression as before.

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

All failure cases are non-blocking, and the session continues normally. When a fallback occurs, an audit log entry is issued: `session_title_fallback session_id=<id> generation=<n> error=<exception class>`. Neither the audit entry nor the logs carry the title text or the raw failure reason, and the fallback title is written only while the session and generation that started the task are still current. Title pending for that session is reset in a `finally` block regardless of the result.

## Responsibility Boundary

### Session Persistence

`AgentSession` owns the `sessions` and `messages` tables (see Design Intent). Schema details: [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md).

### Load-Time Orphan Repair

A turn that was interrupted between the assistant tool-call row and its tool results leaves an assistant row carrying `tool_calls` with no matching `role="tool"` rows in `messages`. `/session load` repairs such an interrupted round in memory before the restored history is installed, so a resumed session never starts with dangling tool calls.

```text
messages (session.sqlite)
        v
assistant row with tool_calls, no matching tool rows?
        v  yes
synthesize the missing tool rows (interrupted-marker content, message whitelist conformant)
        v
replace_history(paired)   # memory-only; DB row count unchanged
```

- **Paired after load.** An assistant row whose `tool_calls` ids are unanswered by the following tool-row run is repaired at load; the restored history ends with that assistant row followed by synthesized tool rows whose `tool_call_id` values match.
- **Synthesis.** Missing tool rows are synthesized in `tool_calls` order, carrying the original `tool_call_id` and an identifiable interrupted-marker content that conforms to the message whitelist. A WARNING names the repaired session. Canonical implementation: `scripts/agent/services/session_restore.py`.
- **Memory-only and idempotent.** No row is written to `messages` at load, so the row count is unchanged and a second load reproduces identical history. Synthesized rows reach the database only through the next compression `replace_messages` (see [agent_04_02](agent_04_02_state-and-persistence-history-compression.md)).
- **Undo floor preserved.** The compression boundary index accounts for synthesized rows inserted before it, so `undo_last_turn()` still lands on the correct turn and messages at or before the boundary are never deleted.

Load-time repair is a distinct, failure-triggered path; it does not change the semantics of `/undo` or of the save rules above.

### Restored Rows on Load

`/session load` rebuilds `ctx.conv.history` from stored messages as
[current system prompt, canonical summary row?, ...non-system rows]:

- **Current system prompt.** The live prompt replaces any persisted prompt row.
- **Canonical summary row.** Exactly one persisted system row whose content starts
  with the shared `CONVERSATION_SUMMARY_PREFIX` (`"[Conversation summary]"`) is
  restored immediately after the current prompt, rebuilt with only `role` and
  `content`. When several summary-shaped rows are persisted, only the most recent
  is kept and a warning names the dropped count. Recognition: `is_conversation_summary()`.
- **Non-system rows.** Every user, assistant, and tool row is restored.
- **Other persisted system rows are dropped.** Only the owner-assigned current
  prompt is trusted; any other persisted system row cannot become an instruction
  (untrusted restore). This is the behavior the Plan preserves.

Ephemeral system rows (`_ephemeral` / `_memory_injected`) are not persisted, so they
are never restored; see [agent_04_02](agent_04_02_state-and-persistence-history-compression.md).

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
  `/session purge` do not modify Episodic Memory.
- Episodic Memory is generated and managed internally; no command gives users add, delete, prune, or rebuild operations (ADR-008).
- `/session export` exports conversation history only. Episodic Memory is backed up and
  recovered only with the Session DB (see agent_09_01), and Repository Context is reloaded
  from the configured files.

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
