# Agent Runtime Architecture

- System overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Describe the major runtime components, their dependency relationships, and responsibility
boundaries so that an engineer or AI can locate where any behavior is implemented.

---

## Component Dependency Diagram

```
agent/__main__.py
  └─ AgentREPL (agent/repl.py)          — REPL coordinator; thin; no business logic
       ├─ AgentContext (agent/context.py) — per-session DI hub; shared mutable state
       │    ├─ AgentConfig               — hot-reloadable runtime configuration
       │    ├─ AgentSession              — SQLite session/message/note persistence
       │    ├─ ConversationState         — history list, LLM URL, flags
       │    ├─ TurnState                 — current turn UUID (reset per turn)
       │    ├─ RuntimeStats              — cumulative session metrics
       │    └─ AppServices               — all service references (injected by factory.py)
       │         ├─ LLMClient            — SSE streaming, retry
       │         ├─ ToolExecutor         — MCP routing, TTL cache
       │         ├─ HistoryManager       — char counting, LLM compression
       │         ├─ _ServerLifecycleRouter — HTTP subprocess + stdio lifecycle
       │         ├─ audit_logger         — JSON-lines audit.log writer
       │         └─ MemoryServices?      — optional semantic memory layer
       ├─ CLIView (agent/cli_view.py)    — readline, progress display, multiline input
       ├─ CommandRegistry                — all /cmd dispatch (10 mixins)
       └─ Orchestrator (agent/orchestrator.py) — turn-level facade
            ├─ LLMTurnRunner             — SSE stream + inner tool-call loop
            └─ ToolLoopGuard             — dedup/cycle/retry/error guards
```

---

## Component Responsibilities

### AgentREPL (`agent/repl.py`)

- Owns startup sequence: readline setup → DI wiring → MCP startup → service health check → REPL loop
- Dispatches each user input to `Orchestrator.handle_turn()` or `CommandRegistry.dispatch()`
- Owns graceful shutdown (SIGTERM → `SystemExit(0)` conversion, `_close_resources()`)
- No business logic; delegates everything to sub-components

**Startup sequence:**

```
_initialize_session()
  → _view.setup_readline()
  → build_agent_context(ctx, view)   [factory.py]
  → _init_command_registry
  → _init_orchestrator
_start_mcp_servers()                 [persistent stdio + HTTP subprocess]
_check_services()
  → check_readiness()              [repl_health.py — raises in production mode if services down]
  → _check_tool_definitions()
_setup_initial_prompt()
  → system prompt init
  → memory.on_session_start()
_run_repl_loop()
```

### Orchestrator (`agent/orchestrator.py`)

- Handles one user turn end-to-end
- Manages memory injection → user message append → history compression → LLM turn
- Delegates LLM streaming + tool loop to `LLMTurnRunner`
- Emits audit log events (`turn_start`, `turn_end`)

| Method | Responsibility |
|---|---|
| `handle_turn(line)` | Top-level turn handler |
| `_handle_turn_start(line)` | Generate turn UUID, emit `turn_start` audit event |
| `_handle_memory_injection(line)` | Inject relevant memories as system messages |
| `_handle_history_compression()` | Compress history if over limit |
| `_handle_llm_turn(llm_url)` | Delegate to `LLMTurnRunner.run()`; handle `LLMTransportError` |
| `_handle_turn_end(...)` | Emit `turn_end` audit event (elapsed_ms, token counts) |

### AgentContext (`agent/context.py`)

Shared mutable state and component reference hub. `factory.build_agent_context()` injects
all services. Sub-structures:

| Sub-structure | Scope | Key contents |
|---|---|---|
| `ctx.conv` | session | `history: list[LLMMessage]`, `plan_mode`, `debug_mode`, `system_prompt_content` |
| `ctx.turn` | per-turn | `current_turn_id: str\|None` (UUID4, None between turns) |
| `ctx.stats` | cumulative | `stat_turns`, `stat_tool_calls`, `stat_latency`, token counts |
| `ctx.cfg` | hot-reload | `AgentConfig` (7 sub-configs) |
| `ctx.session` | session | `AgentSession` (SQLite) |
| `ctx.services` | injected | All service instances (LLMClient, ToolExecutor, etc.) |
| `ctx.tool_result_store` | session | Full tool results (accessible via `/tool show`) |

### LLMClient (`shared/llm_client.py`)

- Builds request payload (messages + tool_defs + temperature + max_tokens)
- SSE streaming with `RobustSSEParser` (incremental UTF-8, heartbeat tracking)
- Reconnect on retryable errors (up to `sse_reconnect_max`)
- Partial completion detection and reporting via `LLMTransportError`

### ToolExecutor (`shared/tool_executor.py`)

- Plugin tool lookup → TTL cache check → `_raw_execute()` (MCP routing)
- Side-effect detection: serializes parallel tool calls when write/delete/shell_run present
- `ToolRouteResolver`: resolves tool name → server key (config-driven → static fallback)
- `McpServerHealthRegistry`: tracks per-server health state (HEALTHY/DEGRADED/UNAVAILABLE)

### HistoryManager (`agent/history.py`)

- Counts conversation history size (chars or tokens)
- Triggers LLM-based summarization when threshold exceeded
- `HistorySelectionPolicy`: selects which turns to compress (importance scoring + categories)
- Protects most recent `history_protect_turns` turn pairs from compression

### CommandRegistry (`agent/commands/registry.py`)

10 mixins, each owning a command group. Dispatches built-in commands first, then plugin commands.

| Mixin | Commands |
|---|---|
| `_SessionMixin` | `/session` |
| `_McpMixin` | `/mcp` |
| `_ConfigMixin` | `/config`, `/stats`, `/set`, `/reload` |
| `_ContextMixin` | `/context`, `/clear`, `/undo`, `/history`, `/system` |
| `_DbMixin` | `/db` |
| `_ToolingMixin` | `/tool`, `/plan` |
| `_NotesMixin` | `/note` |
| `_DebugMixin` | `/debug` |
| `_AuditMixin` | `/audit` |
| `_IngestMixin` | `/ingest`, `/export`, `/compact`, `/rag` |
| `_MemoryMixin` | `/memory` |

### CLIView (`agent/cli_view.py`)

- Presentation layer only; no business logic
- Provides `Writer` and `Reader` protocols for testability
- Callbacks injected into `Orchestrator`, `HistoryManager`, `LLMClient`

### AgentSession (`agent/session.py`)

- CRUD for `sessions`, `messages`, `notes` tables
- RAG document delete/list (delegated from `/db` commands)
- `fetch_messages(session_id)` returns `list[LLMMessage]` for session restore

### Memory Services (`agent/memory/`)

Optional subsystem activated by `use_memory_layer=True`.
Accessed via `ctx.services.memory`.

| Sub-service | Role |
|---|---|
| `injection` | Injects relevant memories at session start and per-turn |
| `ingestion` | Extracts and persists memories at session end |
| `store` | JSONL + SQLite store for memory entries |
| `retriever` | FTS5 + optional KNN retrieval |

---

## Spec Conflict: `repl_tool_exec.py` Deletion

**Spec Conflict:**
- `05_agent-impl-class.md` note says `repl_tool_exec.py` is deleted; tool logic moved to
  `shared/tool_executor.py`.
- `05_ref-agent-repl.md` §4 confirms the same.
- **Preferred source:** `05_ref-agent-repl.md` (canonical).
- **Safe interpretation:** Do not reference `agent/repl_tool_exec.py`. Use `ToolExecutor.execute()`.

## Spec Conflict: `ServerLifecycleManager` Deletion

**Spec Conflict:**
- `04_spec_mcp.md §10.5` notes `ServerLifecycleManager` was deleted from `agent/lifecycle.py`.
- `_ServerLifecycleRouter` in `factory.py` took over routing. Only `restart_stdio()` remains in `agent/lifecycle.py`.
- **Safe interpretation:** Use `_ServerLifecycleRouter` for lifecycle. Do not use `ServerLifecycleManager`.
