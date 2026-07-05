# Agent State and Persistence

- Runtime architecture → [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- Turn flow → [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md)
- Data layer (schema) → [05_agent_09_data-layer.md](05_agent_09_data-layer.md)

## Purpose

Define the agent's state model: what is session-scoped vs turn-scoped vs persisted,
how history compression interacts with the database, and who owns what data.

---

## AgentContext State Model

`AgentContext` (`agent/context.py`) is the per-session DI hub. All mutable state lives here.

### ConversationState (`ctx.conv`)

Session-scoped. Persists for the REPL lifetime.

| Field | Type | Initial | Description |
|---|---|---|---|
| `history` | `list[LLMMessage]` | `[]` | Active conversation history (system/user/assistant/tool) |
| `llm_url` | `str` | `""` | Active LLM endpoint URL |
| `debug_mode` | `bool` | `False` | Debug output flag |
| `plan_mode` | `bool` | `False` | Plan mode; blocks `plan_blocked_tools` |
| `system_prompt_name` | `str` | `"default"` | Active system prompt preset name |
| `system_prompt_content` | `str` | `""` | Full system prompt text; synced to `history[0]` per turn |
| `shutdown_requested` | `bool` | `False` | Graceful shutdown flag |

### TurnState (`ctx.turn`)

Turn-scoped. Reset between turns.

| Field | Type | Initial | Description |
|---|---|---|---|
| `current_turn_id` | `str\|None` | `None` | UUID4 set at turn start; `None` between turns |
| `background_tasks` | `set[asyncio.Task[Any]]` | `set()` | Background tasks spawned during this turn; tracked for clean shutdown |
| `last_error_kind` | `str\|None` | `None` | Error kind from the most recent turn failure; `None` when last turn succeeded |
| `pending_approval_id` | `str\|None` | `None` | Approval ID when the last workflow turn was suspended for human approval |

### WorkflowState (`ctx.workflow`)

Session-scoped workflow runtime state. Transient — not persisted across REPL restarts.
Durable task state lives in `workflow.sqlite` (via `StateStore`).

| Field | Type | Initial | Description |
|---|---|---|---|
| `active` | `bool` | `False` | `True` while `WorkflowEngine.run()` is executing |
| `current_task_id` | `str\|None` | `None` | Task ID of the running workflow task; `None` when idle |
| `workflow_id` | `str\|None` | `None` | UUID4 for this workflow run; `None` when idle |
| `current_workflow_version` | `str\|None` | `None` | Workflow version string from `WorkflowDef` |
| `approval_pending` | `bool` | `False` | `True` when the turn was suspended at an approval gate |
| `last_session_id` | `str\|None` | `None` | Session ID used on the most recent `create_task()` call |

`Orchestrator.handle_turn()` sets `active=True` and `current_task_id` on task creation;
clears both after engine completion or `WorkflowHaltError`.
`approval_pending=True` is set on `WorkflowPendingApprovalError` (turn suspended).

### RuntimeStats (`ctx.stats`)

Session-cumulative counters and latency samples.

| Field | Type | Description |
|---|---|---|
| `stat_turns` | `int` | User turns count |
| `stat_tool_calls` | `int` | Tool call count |
| `stat_tool_errors` | `int` | Tool error count |
| `stat_latency` | `dict[str, list[float]]` | Step-level latency samples (seconds) |
| `stat_semantic_cache_hits` | `int` | Semantic cache hits |
| `stat_input_tokens` | `int\|None` | LLM input tokens (`None` if endpoint omits `usage`) |
| `stat_output_tokens` | `int\|None` | LLM output tokens (`None` if endpoint omits `usage`) |
| `stat_serialization_events` | `list[dict]` | Per-round serialization events recorded by the DAG tool scheduler and standard runner. Accumulated across all turns. Initial: `[]`. Surfaced by the `/mcp` command. |
| `stat_serialization_total_overhead_ms` | `float` | Total serialization overhead in milliseconds, accumulated across all turns. Initial: `0.0`. |
| `stat_memory_consistency_failures` | `int` | Count of `/memory check-consistency` failures this session. Incremented by `cmd_memory.py`. Initial: `0`. |
| `stat_memory_circuit_open` | `bool` | `True` when the memory embedding circuit breaker is open. Read at display time from `MemoryServices` via `cmd_config_stats._get_mem_circuit_open()` — **not written to `ctx.stats`** during normal operation. Initial: `False`. |
| `stat_memory_fts_fallback_count` | `int` | Count of FTS fallbacks this session (triggered when embedding is unavailable). Mirrors `MemoryServices.retriever.fts_fallback_count` — read at display time via `cmd_config_stats._get_mem_fts_fallback()`, not independently tracked in `ctx.stats`. Initial: `0`. |

---

## Session Persistence (`AgentSession`)

`AgentSession` (`agent/session.py`) manages `session.sqlite`.

### What is persisted per turn

| Event | Table | Content |
|---|---|---|
| Session start | `sessions` | session_id, created_at, title |
| Each message | `messages` | role, content, tool_calls, tool_call_id, session_id |

### Session lifecycle

```
AgentREPL.run()
  → AgentSession.start()              — INSERT into sessions; get session_id
  → each turn: AgentSession.save()    — INSERT into messages
  → /session load <id>                — fetch_messages() → rebuild ctx.conv.history
  → /session delete <id>              — DELETE sessions + messages (CASCADE)
```

### Session title generation

On the first user turn, `_generate_session_title()` (in `cmd_session.py`) calls `SessionTitleService.generate()` to produce an LLM-based short title. This runs as an asyncio background task (fire-and-forget via `asyncio.create_task()`).

### Session Title Generation Failure Behavior

| Failure case | Fallback title | Log |
|---|---|---|
| LLM HTTP / request error | `first_input[:29] + "..."` if len > 32, else `first_input` | WARNING |
| LLM returns empty or invalid response | Same as above | WARNING |
| `first_input` is empty | `"(New Session)"` | WARNING |
| `set_title()` DB write fails | No title persisted; error logged | ERROR |

All failure cases are non-blocking — the session continues normally.
On fallback, an audit log entry is emitted: `session_title_fallback session_id=<id> fallback=<title> reason=<error>`.
`set_title_pending` is reset to `False` in the `finally` block regardless of outcome.

### Message save rules

- `save(role, content)` saves only valid roles: `user`, `assistant`, `tool`, `system`
- Invalid roles are logged as warnings and counted (`stat_skipped_invalid_role`)
- Missing `session_id` is logged as a warning and counted (`stat_skipped_no_session`)
- When `strict_mode=True`, both conditions raise `RuntimeError` instead of skipping
- Counters accessible via `session.skipped_no_session_count` and `session.skipped_invalid_role_count`
- `save_many(messages)` batches multiple messages in one transaction; invalid roles are skipped with a single warning log
- `replace_messages(messages)` persists compressed history snapshot back to DB; skips silently if session_id is None
- Diagnostic data (LLM transport errors, guard hints, session runtime summaries) is persisted via `DiagnosticStore` (`agent/diagnostic_store.py`) to the `session_diagnostics` table — separate from the `messages` table. For the partial-completion persistence model → [05_agent_03 §Partial-Completion Model](05_agent_03_turn-processing-flow.md)
- `DiagnosticStore` methods: `save(session_id, kind, content)`, `fetch(session_id)`, `fetch_all(limit=50)`
- `AgentContext.diagnostics` is wired to `Orchestrator._diagnostic_store` on init; `None` before any `Orchestrator` is constructed
- Kinds written: `"mid_turn_error"` (LLM transport errors from `ErrorInjectionService`, `LLMTurnRunner`, `Orchestrator`), `"guard_hint"` (cycle/dedup/retry events from `ToolLoopGuard`)
- Guard hints and mid-turn errors are stored only in diagnostics — they do NOT appear in `ctx.conv.history`
- Diagnostic data is stored in the `session_diagnostics` table via `DiagnosticStore`; it is never present in `messages` and therefore never returned by `fetch_messages()`

> **Current behavior:** DiagnosticStore writes to the `session_diagnostics` table only. Diagnostics are persisted exclusively through `session_diagnostics` — there is no dual persistence to `diagnostics.jsonl`.

---

## Relationship Between Conversation History and Database

```
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- History is the authoritative source during a session
- Database is the persistent backup
- `/session load <id>` reconstructs `ctx.conv.history` from database
- `delete_last_turn()` removes last 2 rows (up to 2) from DB
- `undo_last_turn()` removes everything from the last `role='user'` message onwards

---

## HistoryManager Compression

`HistoryManager` (`agent/history.py`) manages compression of `ctx.conv.history`.

### Compression trigger

Triggered in `_handle_history_compression()` each turn if either:
- `len(history_chars) > context_char_limit` (default 8000)
- `token_count > context_token_limit` (if > 0)

### Compression selection

`HistorySelectionPolicy.select_turns_to_compress()` selects turns by:
1. Importance scoring (pinned → explicit importance → keyword-based)
2. Category classification:
   - `temporary` (tool role) — highest removal priority
   - `temporary_reasoning` (assistant with tool_calls) — second priority
   - `factual` (system) — preserved
   - `history` (user/assistant text) — normal priority
3. The most recent `history_protect_turns` (default 2) user+assistant pairs are exempt

### Compression result

- Selected old turns → replaced with one LLM summary message
- `CompressResult.compressed_count` = number of messages replaced
- `CompressResult.protected_count` = number of messages skipped (protected)
- `stat_compress_count` incremented

### Compression Persistence Model

After each history compression (automatic or `/compact`), the compressed snapshot is persisted back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state — the restored history matches what was actually in context before the next LLM call.

Key behaviors:
- Compressed `[Conversation summary]` system messages are persisted as `role=system` rows; they round-trip correctly through `fetch_messages()` → `LLMMessage`.
- Fallback truncation (drop-without-summary) also triggers persistence to keep DB consistent.
- The in-memory `ctx.conv.history` remains the source of truth for the current session; DB persistence is a backup for reload scenarios.
- `/history` and `/export` continue to operate on `ctx.conv.history`; no change needed.
- The `stat_turns` counter and other in-memory stats reset on reload (existing behavior).

**Note**: After a reload of a compressed session, `/undo` operates on the compressed DB rows — the user may undo fewer turns than expected since the original messages were replaced by the summary message.

### Token counting

Priority: (1) LLM `usage.input_tokens` (exact); (2) `/tokenize` endpoint (exact);
(3) `chars // 4` fallback.

### HistoryManager API (key methods)

| Method | Description |
|---|---|
| `count_chars(history)` | Total chars (content + tool_calls JSON) |
| `count_tokens(history, last_input_tokens)` | Sync token estimate |
| `count_tokens_async(...)` | Async token count; returns `(count, is_exact)` |
| `compress(history)` | Compress if over limit; returns `(new_history, CompressResult)` |
| `force_compress(history)` | Compress immediately regardless of limit (`/compact` cmd) |
| `apply_config(...)` | Hot-reload: char_limit, compress_turns, token_limit, tokenize_url |

### Compression Persistence Model

After each history compression (automatic or `/compact`), the compressed snapshot is persisted back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state — the restored history matches what was actually in context before the next LLM call.

Key behaviors:
- Compressed `[Conversation summary]` system messages are persisted as `role=system` rows; they round-trip correctly through `fetch_messages()` → `LLMMessage`.
- Fallback truncation (drop-without-summary) also triggers persistence to keep DB consistent (`CompressResult.is_fallback=True`).
- The in-memory `ctx.conv.history` remains the source of truth for the current session; DB persistence is a backup for reload scenarios.
- `/history` and `/export` continue to operate on `ctx.conv.history`; no change needed.
- The `stat_turns` counter and other in-memory stats reset on reload (existing behavior).

**Note**: After a reload of a compressed session, `/undo` operates on the compressed DB rows — the user may undo fewer turns than expected since the original messages were replaced by the summary message.

---

## Data Classification

| Data type | Scope | Storage | When persisted | Cleared by |
|---|---|---|---|---|
| `ctx.conv.history` | session | in-memory | Per message (async, before LLM call) | `/clear` or session end |
| `ctx.conv.*` flags | session | in-memory | — (not persisted) | session restart |
| `ctx.turn.current_turn_id` | turn | in-memory | — (not persisted) | end of each turn |
| `ctx.stats.*` | session | in-memory | — (reported via `/stats`) | `/clear` |
| `sessions` table | persistent | SQLite | On session create; title async on first turn | `/session delete` |
| `messages` table | persistent | SQLite | Per `AgentSession.save()` call | `/session delete` or `/undo` |
| `ctx.tool_result_store` | session | in-memory + SQLite | Each tool call result stored immediately | session end |
| Memory JSONL / `memories` table | persistent | JSONL + SQLite | On memory extraction (async) | `/memory delete` or `/memory prune` |

---

## Platform Databases

The agent layer operates across three SQLite databases:

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | Agent sessions, messages | `90_shared_04` §2 |
| `rag.sqlite` | RAG documents, chunks, embeddings | `90_shared_04` §3-§6 |
| `workflow.sqlite` | Task tracking, event processing | `90_shared_04` §7 |

DB paths are configured via `rag_db_path`, `session_db_path`, `workflow_db_path` in `common.toml`. Full schema details: `90_shared_04_db_architecture_and_schema.md`.

**DB ownership:**

| Database | Owner module | Key class |
|---|---|---|
| `session.sqlite` | `agent/session.py` | `AgentSession` |
| `workflow.sqlite` | `agent/workflow/state_store.py` | `StateStore` |
| `rag.sqlite` | `scripts/mcp/rag_pipeline/` | RAG MCP server |

> **Note:** The `/db session` scope covers session.sqlite maintenance. `/db` does not expose workflow.sqlite for direct maintenance — workflow state is managed exclusively by `StateStore` via `WorkflowEngine`.

### StateStore methods (`agent/workflow/state_store.py`)

| Method | Description |
|---|---|
| `create_task(session_id, turn_number, workflow_version, workflow_id)` | Create a new task record; returns `TaskRecord` |
| `update_task_status(task_id, status)` | Update task status (pending/running/pending_approval/completed/failed/halted) |
| `get_task_by_id(task_id)` | Return the task record for the given task_id, or None if absent |
| `get_task_by_idempotency_key(key)` | Return the task record for the given idempotency key, or None |
| `get_task_by_session(session_id)` | Return all tasks for a session ordered by created_at ascending |
| `get_latest_task(session_id)` | Return the most recently created task for a session |
| `list_tasks(limit=50)` | Return up to `limit` tasks ordered by created_at descending |
| `start_attempt(task_id, stage_id)` | Start a new attempt record; returns `AttemptRecord` |
| `finish_attempt(attempt_id, status, error_msg)` | Complete an attempt with status and optional error message |
| `count_attempts(task_id, stage_id)` | Return count of attempts for a task+stage combination |

### Task CRUD operations (`agent/workflow/task_ops.py`)

| Function | Description |
|---|---|
| `create_task(db, session_id, turn_number, workflow_version, workflow_id)` | Create a new task record; returns `TaskRecord` |
| `update_task_status(db, task_id, status)` | Update task status (pending/running/pending_approval/completed/failed/halted) |
| `get_task_by_id(db, task_id)` | Return the task record for the given task_id, or None if absent |
| `get_task_by_idempotency_key(db, key)` | Return the task record for the given idempotency key, or None |
| `get_task_by_session(db, session_id)` | Return all tasks for a session ordered by created_at ascending |
| `get_latest_task(db, session_id)` | Return the most recently created task for a session |
| `list_tasks(db, limit=50)` | Return up to `limit` tasks ordered by created_at descending |

### Attempt operations (`agent/workflow/attempt_ops.py`)

| Function | Description |
|---|---|
| `start_attempt(db, task_id, stage_id)` | Start a new attempt record; returns `AttemptRecord` |
| `finish_attempt(db, attempt_id, status, error_msg)` | Complete an attempt with status and optional error message |
| `count_attempts(db, task_id, stage_id)` | Return count of attempts for a task+stage combination |

### Approval operations (`agent/workflow/approval_ops.py`)

| Function | Description |
|---|---|
| `request_approval(db, task_id, stage_id)` | Insert a pending approval gate for a task (or specific stage); returns `ApprovalRecord` |
| `resolve_approval(db, approval_id, status, reason)` | Set approval status to 'approved' or 'rejected' |
| `get_pending_approval(db, task_id)` | Return the most recent approval record for a task, or None if absent |
| `find_pending_approval_by_session(db, session_id)` | Return (task_id, approval) for the most recent pending-approval task in this session, or None |
| `find_latest_pending_approval(db)` | Return (task_id, approval) for the most recent globally pending approval, or None |

### Artifact operations (`agent/workflow/artifact_ops.py`)

| Function | Description |
|---|---|
| `record_artifact(db, task_id, stage_id, uri)` | Record an artifact reference; returns `ArtifactRef` |

### Idempotency operations (`agent/workflow/idempotency_ops.py`)

| Function | Description |
|---|---|
| `is_event_processed(db, event_id)` | Check if an event has already been processed (idempotency guard) |
| `begin_stage_if_new(db, event_id, task_id, stage_id)` | Atomically check event_id and start attempt if new; returns `AttemptRecord` if the stage should run, None if already processed |

### WorkflowLoader constants (`agent/workflow/workflow_loader.py`)

| Constant | Value |
|---|---|
| `_REQUIRED_STAGE_KEYS` | `{"id", "description", "timeout_sec", "retryable"}` — required keys per stage definition |
| `_REQUIRED_POLICY_KEYS` | `{"max_attempts", "backoff", "backoff_sec"}` — required keys per retry policy |
| `_REQUIRED_STAGES` | `{"plan", "execute", "verify"}` — required stages in the workflow |
| `_SUPPORTED_BACKOFF` | `{"fixed", "exponential"}` — supported backoff strategies |

---

## Session / RAG Responsibility Boundary

`AgentSession` (`agent/session.py`) has zero RAG-layer imports or methods.
All RAG document operations (ingest, search, chunk management) go through the
RAG MCP path; RAG maintenance operations go through `RagMaintenanceService` —
never through the session object.

### Service responsibility boundary

| Service | DB | Methods |
|---|---|---|
| `DbMaintenanceService` | session.sqlite | `stats` (sessions/messages), `health`, `checkpoint`, `vacuum`, `purge`, `recover_session` |
| `RagMaintenanceService` | rag.sqlite | `stats_rag` (docs/chunks), `rebuild_fts`, `consistency`, `recover`, `rebuild_vec`, `reconcile_url` |

`AgentSession` accesses only session.sqlite via `SQLiteHelper("session")`.

Verified boundaries:
- `agent/session.py` imports only: `db.helper`, `shared.types`, `agent.session_message_repo`
- `db/maintenance.py` contains RAG-file utility functions (`rotate_rag_db`, `vacuum_db`) but has zero `rag/` module imports
- `/db` command routes subcommands by scope: `/db rag <subcmd>` targets `RagMaintenanceService`; `/db session <subcmd>` targets `DbMaintenanceService`
