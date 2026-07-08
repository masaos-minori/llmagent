# Agent Runtime Architecture

- System overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Describe the major runtime components, their dependency relationships, and responsibility
boundaries so that an engineer or AI can locate where any behavior is implemented.

> **Scope of this chapter:** runtime behavior, module graph, data flow, and component lifecycles.
> For function signatures, parameter types, and return values → [05_agent_13 §Reference API](05_agent_13_reference-api.md).

---

## Component Dependency Diagram

```
agent/__main__.py
  └─ AgentREPL (agent/repl.py)          — REPL coordinator; input loop + output only
       ├─ StartupOrchestrator (agent/startup.py) — startup sequence; created once in run()
       ├─ AgentContext (agent/context.py) — per-session DI hub; shared mutable state
       │    ├─ AgentConfig               — hot-reloadable runtime configuration
       │    ├─ AgentSession              — SQLite session/message persistence
       │    ├─ ConversationState         — history list, LLM URL, flags
       │    ├─ TurnState                 — current turn UUID (reset per turn)
       │    ├─ RuntimeStats              — cumulative session metrics
       │    ├─ WorkflowState             — active task ID, approval_pending flag (transient)
       │    └─ AppServices               — all service references (injected by factory.py)
       │         ├─ LLMClient            — SSE streaming, retry
       │         ├─ ToolExecutor         — MCP routing, TTL cache
       │         ├─ HistoryManager       — char counting, LLM compression
       │         ├─ ServerLifecycleRouter — HTTP subprocess lifecycle
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

- Owns the input/dispatch loop: read line → command or LLM turn
- Delegates entire startup sequence to `StartupOrchestrator`
- Owns graceful shutdown (SIGTERM → `SystemExit(0)` conversion)
- No business logic; contains only UI loop, command dispatch, and output display

**Startup sequence (delegated to `StartupOrchestrator.run()`):**

```
StartupOrchestrator.run()
  Initialization phase:
    → Readline setup
    → build_agent_context(ctx, view)   [factory.py]
    → Command registry initialization
    → Orchestrator initialization
  MCP server startup                 [HTTP subprocess MCP servers]
  Prompt setup
    → system prompt init
    → memory.on_session_start()
→ returns (CommandRegistry, Orchestrator)
REPL loop
```

### StartupOrchestrator (`agent/startup.py`)

- Houses all startup orchestration extracted from `AgentREPL`
- Constructed with `(ctx, view)`; `run()` returns `(CommandRegistry, Orchestrator)`
- Isolates startup complexity so `AgentREPL` contains only UI concerns

### Orchestrator (`agent/orchestrator.py`)

- Handles one user turn end-to-end
- Manages memory injection → user message append → history compression → LLM turn
- Delegates LLM streaming + tool loop to `LLMTurnRunner`
- Emits audit log events (`turn_start`, `turn_end`)

| Method | Responsibility |
|---|---|
| `handle_turn(line)` | Top-level turn handler |

### AgentContext (`agent/context.py`)

Shared mutable state and component reference hub. `factory.build_agent_context()` injects
all services. Sub-structures:

| Sub-structure | Scope | Key contents |
|---|---|---|
| `ctx.conv` | session | `history: list[LLMMessage]`, `plan_mode`, `debug_mode`, `system_prompt_content` |
| `ctx.turn` | per-turn | `current_turn_id: str\|None` (UUID4, None between turns) |
| `ctx.stats` | cumulative | `stat_turns`, `stat_tool_calls`, `stat_latency`, token counts |
| `ctx.workflow` | session | `WorkflowState`: `active`, `current_task_id`, `workflow_id`, `approval_pending` (transient) |
| `ctx.cfg` | hot-reload | `AgentConfig` (7 sub-configs) |
| `ctx.session` | session | `AgentSession` (SQLite) |
| `ctx.services` | injected | All service instances (LLMClient, ToolExecutor, etc.) |
### LLMClient (`shared/llm_client.py`)

- Builds request payload (messages + tool_defs + temperature + max_tokens)
- SSE streaming with `RobustSSEParser` (incremental UTF-8, heartbeat tracking)
- Reconnect on retryable errors (up to `sse_reconnect_max`)
- Partial completion detection and reporting via `LLMTransportError`

### ToolExecutor (`shared/tool_executor.py`)

- Plugin tool lookup → TTL cache check → MCP routing
- Side-effect detection: serializes parallel tool calls when write/delete/shell_run present
- `ToolRouteResolver`: resolves tool name → server key (live `/v1/tools` discovery → ToolRegistry)
- `McpServerHealthRegistry`: tracks per-server health state (HEALTHY/DEGRADED/UNAVAILABLE)

### HistoryManager (`agent/history.py`)

- Counts conversation history size (chars or tokens)
- Triggers LLM-based summarization when threshold exceeded
- `HistorySelectionPolicy`: selects which turns to compress (importance scoring + categories)
- Protects most recent `history_protect_turns` turn pairs from compression
- `compress_turns` property: number of oldest turn pairs selected for compression

### CommandRegistry (`agent/commands/registry.py`)

12 mixins, each owning a command group. Dispatches built-in commands first, then plugin commands.

| Mixin | Commands |
|---|---|
| `SessionMixin` | `/session` |
| `McpMixin` | `/mcp` |
| `ConfigMixin` | `/config`, `/stats`, `/set`, `/reload` |
| `ContextMixin` | `/context`, `/clear`, `/undo`, `/history`, `/system` |
| `DbMixin` | `/db` |
| `ToolingMixin` | `/plan` |
| `DebugMixin` | `/debug` |
| `AuditMixin` | `/audit` |
| `RagExportMixin` | `/rag`, `/export`, `/compact` |
| `MemoryMixin` | `/memory` |
| `WorkflowMixin` | `/approve`, `/reject` |

### CLIView (`agent/cli_view.py`)

- Presentation layer only; no business logic
- Provides `Writer` and `Reader` protocols for testability
- Callbacks injected into `Orchestrator`, `HistoryManager`, `LLMClient`

### LifecycleState (`agent/lifecycle.py`)

Transport state enum shared by lifecycle managers:

| Value | Description |
|---|---|
| `STARTING` | Server starting up |
| `RUNNING` | Server is operational |
| `STOPPED` | Server has been stopped |
| `FAILED` | Server encountered an error |
| `UNKNOWN` | Initial/unknown state |

Valid transitions: `STOPPED → STARTING/FAILED`, `STARTING → RUNNING/FAILED/STOPPED`, `RUNNING → STOPPED/FAILED/STARTING`, `FAILED → STARTING/STOPPED`, `UNKNOWN → any`.

`assert_valid_transition(from_state, to_state)` raises `ValueError` when the transition is illegal.

### AgentSession (`agent/session.py`)

- CRUD for `sessions`, `messages` tables
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

