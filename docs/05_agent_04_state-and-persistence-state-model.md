---
title: "Agent State and Persistence"
category: agent
tags:
  - agent
  - agent
  - state
  - persistence
  - session
  - history
related:
  - 05_agent_00_document-guide.md
---

# Agent State and Persistence

AgentContext` (`agent/context.py`) is the per-session DI hub. All mutable state lives here.

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
| `stat_memory_circuit_open` | `bool` | `True` when the memory embedding circuit breaker is open. Read at display time from `MemoryServices` — **not written to `ctx.stats`** during normal operation. Initial: `False`. |
| `stat_memory_fts_fallback_count` | `int` | Count of FTS fallbacks this session (triggered when embedding is unavailable). Mirrors `MemoryServices.retriever.fts_fallback_count` — read at display time, not independently tracked in `ctx.stats`. Initial: `0`. |

---

## Session Persistence (`Agent

Session`)

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

On the first user turn, session title generation in `cmd_session.py` calls `SessionTitleService.generate()` to produce an LLM-based short title. This runs as an asyncio background task (fire-and-forget via `asyncio.create_task()`).

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
- `AgentContext.diagnostics` is wired to the orchestrator's diagnostic store on init; `None` before any `Orchestrator` is constructed
- Kinds written: `"mid_turn_error"` (LLM transport errors from `ErrorInjectionService`, `LLMTurnRunner`, `Orchestrator`), `"guard_hint"` (cycle/dedup/retry events from `ToolLoopGuard`)
- Guard hints and mid-turn errors are stored only in diagnostics — they do NOT appear in `ctx.conv.history`
- Diagnostic data is stored in the `session_diagnostics` table via `DiagnosticStore`; it is never present in `messages` and therefore never returned by `fetch_messages()`

> **Current behavior:** DiagnosticStore writes to the `session_diagnostics` table only. Diagnostics are persisted exclusively through `session_diagnostics` — there is no dual persistence to `diagnostics.jsonl`.

---

## Relationship Between Conver

## Related Documents

- `agent`
- `state`
- `persistence`

## Keywords

agent
state
persistence
session
history
