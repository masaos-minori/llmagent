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

---

## Session Persistence (`AgentSession`)

`AgentSession` (`agent/session.py`) manages `session.sqlite`.

### What is persisted per turn

| Event | Table | Content |
|---|---|---|
| Session start | `sessions` | session_id, created_at, title |
| Each message | `messages` | role, content, tool_calls, tool_call_id, session_id |
| Note operations | `notes` | note_id, content, created_at |

### Session lifecycle

```
AgentREPL.run()
  → AgentSession.start()              — INSERT into sessions; get session_id
  → each turn: AgentSession.save()    — INSERT into messages
  → /session load <id>                — fetch_messages() → rebuild ctx.conv.history
  → /session delete <id>              — DELETE sessions + messages (CASCADE)
```

### Session title generation

On the first user turn, `_generate_session_title()` (in `cmd_session.py`) calls `SessionTitleService.generate()` to produce an LLM-based short title. This runs as a background task.

If LLM generation fails (`SessionTitleGenerationError`), a fallback title is derived from `first_input`:
- Truncated to `SESSION_TITLE_MAX_CHARS` (32 characters)
- Appended with `...` if the original input exceeds the limit
- Persisted via `ctx.session.set_title()`

This guarantees every session has a non-empty, meaningful title even when the LLM endpoint is unavailable.

### Message save rules

- `save(role, content)` saves only valid roles: `user`, `assistant`, `tool`, `system`
- Invalid roles are logged as warnings and counted (`stat_skipped_invalid_role`)
- Missing `session_id` is logged as a warning and counted (`stat_skipped_no_session`)
- When `strict_mode=True`, both conditions raise `RuntimeError` instead of skipping
- Counters accessible via `session.skipped_no_session_count` and `session.skipped_invalid_role_count`
- `save_many()` batches multiple messages in one transaction; invalid roles are skipped with a single warning log
- Diagnostic data (LLM transport errors, guard hints, session runtime summaries) is persisted via `DiagnosticStore` (`agent/diagnostic_store.py`) to the `session_diagnostics` table — separate from the `messages` table
- `DiagnosticStore` methods: `save(session_id, kind, content)`, `fetch(session_id)`, `fetch_all(limit=50)`
- `AgentContext.diagnostics` is wired to `Orchestrator._diagnostic_store` on init; `None` before any `Orchestrator` is constructed
- Kinds written: `"mid_turn_error"` (LLM transport errors from `ErrorInjectionService`, `LLMTurnRunner`, `Orchestrator`), `"guard_hint"` (cycle/dedup/retry events from `ToolLoopGuard`)
- Guard hints and mid-turn errors are stored only in diagnostics — they do NOT appear in `ctx.conv.history`
- A lightweight session summary is also written to `<session_db_dir>/diagnostics.jsonl` by `repl.py` (may be deprecated in future)
- `fetch_messages()` no longer filters out `diagnostic` role — diagnostic data is in its own table

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

---

## Data Classification

| Data type | Scope | Storage | Cleared by |
|---|---|---|---|
| `ctx.conv.history` | session | in-memory | `/clear` or session end |
| `ctx.conv.*` flags | session | in-memory | session restart |
| `ctx.turn.current_turn_id` | turn | in-memory | end of each turn |
| `ctx.stats.*` | session | in-memory | `/clear` |
| `sessions` table | persistent | SQLite | `/session delete` |
| `messages` table | persistent | SQLite | `/session delete` or `/undo` |
| `notes` table | persistent | SQLite | `/note delete` |
| `ctx.tool_result_store` | session | in-memory | session end |
| Memory JSONL / `memories` table | persistent | JSONL + SQLite | `/memory delete` or `/memory prune` |

---

## Platform Databases

The agent layer operates across three SQLite databases:

| Database | Purpose | Schema reference |
|---|---|---|
| `session.sqlite` | Agent sessions, messages, notes | `06_shared_04` §2 |
| `rag.sqlite` | RAG documents, chunks, embeddings | `06_shared_04` §3-§6 |
| `workflow.sqlite` | Task tracking, event processing | `06_shared_04` §7 |

DB paths are configured via `rag_db_path`, `session_db_path`, `workflow_db_path` in `common.toml`. Full schema details: `06_shared_04_db_architecture_and_schema.md`.

---

## Session / RAG Responsibility Boundary

`AgentSession` (`agent/session.py`) has zero RAG-layer imports or methods.
All RAG document operations (ingest, search, chunk management, DB maintenance) go
through `DbMaintenanceService` (`agent/services/db_maintenance_service.py`) or the
RAG MCP path — never through the session object.

Verified boundaries:
- `agent/session.py` imports only: `db.helper`, `shared.types`, `agent.note_repo`, `agent.session_message_repo`
- `db/maintenance.py` contains RAG-file utility functions (`rotate_rag_db`, `vacuum_db`) but has zero `rag/` module imports
- `/db` command routes all RAG subcommands through `DbMaintenanceService`, not through `AgentSession`
