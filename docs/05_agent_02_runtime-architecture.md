# Agent Runtime Architecture (Part 1)

- System Overview $\rightarrow$ [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Describes the primary runtime components, their dependencies, and responsibility boundaries, enabling engineers and AI to identify where specific behaviors are implemented.

> **Scope of this chapter:** Runtime behavior, module graph, data flow, and component lifecycles. For function signatures, parameter types, and return values $\rightarrow$ see [05_agent_13 Reference API](05_agent_13_reference-api.md).

## Responsibility Boundary

### Component Dependencies

``` text
AgentREPL (agent/repl.py)          — REPL coordinator; input loop + output only
   ├─ StartupOrchestrator (agent/startup.py) — startup sequence; created once in run()
   ├─ AgentContext (agent/context.py) — per-session DI hub; shared mutable state
   │    ├─ LLMClient            — SSE streaming, retry
    │    ├─ ToolExecutor         — MCP routing
   │    ├─ HistoryManager       — char counting, LLM compression
   │    └─ ServerLifecycleRouter — HTTP subprocess lifecycle
   ├─ CLIView (agent/cli_view.py)    — readline, progress display, multiline input
   └─ Orchestrator (agent/orchestrator.py) — turn-level facade
        └─ LLMTurnRunner             — SSE stream + inner tool-call loop
```

### Responsibility Boundary Supplement

- `AgentContext` is the hub for shared mutable state and component references. `factory.build_agent_context()` injects all services.
- `Orchestrator` handles end-to-end processing of a single user turn, delegating LLM streaming and the tool loop to `LLMTurnRunner`.
- The runtime implementation of `AppServices.lifecycle` is defined in `agent/factory.py`; starting and stopping HTTP subprocesses is delegated to `agent/http_lifecycle.py`.

## Key Constraints

- `Orchestrator.__init__()` loads workflow definitions via `WorkflowLoader().load()`, raising a `RuntimeError` on failure (which stops startup).
- If an exception occurs after starting an MCP subprocess, the started MCP subprocesses are rolled back.
- Side-effect detection: if `write`/`delete`/`shell_run` is included, parallel tool calls are serialized.

## Operational Notes

- `AgentContext.diagnostics` is an attribute not shown in the diagram above, which is set after `Orchestrator.__init__()` execution.
- `handle_turn()` executes the plan/execute/verify stages via the workflow engine. New turns are rejected while `ctx.workflow.approval_pending` is `True` or while background tasks are paused. (See [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md) for details.)

## Known Limitations

- Notification and pause mechanisms when background task failure thresholds are reached are opt-in (disabled by default). (See [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md) for details.)

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture.md`

## Keywords

agent
runtime
architecture
lifecycle

# Agent Runtime Architecture (Part 2)

- System Overview $\rightarrow$ [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Describes runtime extension points, lifecycle phases, and shutdown policies, clarifying component operation duration and interdependencies.

## Design Intent

`AgentREPL` is responsible only for the UI loop, command dispatching, and output display, containing no business logic. By delegating all startup sequences to `StartupOrchestrator`, the REPL functions purely as an I/O layer.

Decoupling `StartupOrchestrator` from `AgentREPL` allows complexity during startup (service checks, MCP server startup, approval recovery) to be separated from the REPL's responsibility, ensuring the REPL focuses solely on UI concerns.

## Responsibility Boundary

### Component Responsibilities

#### AgentREPL (`agent/repl.py`)

- Manages the input/dispatch loop: reads lines $\rightarrow$ commands or LLM turns.
- Manages graceful shutdown.
- Contains no business logic. Responsible only for UI loop, command dispatch, and output display.

#### StartupOrchestrator (`agent/startup.py`)

- Encapsulates all startup orchestration processes extracted from `AgentREPL`.
- Constructed with `(ctx, view)`. `run()` returns `(CommandRegistry, Orchestrator)`.
- Decouples startup complexity so that `AgentREPL` remains focused on UI concerns.

#### Orchestrator (`agent/orchestrator.py`)

- Handles end-to-end processing of a single user turn.
- Manages the flow: memory injection $\rightarrow$ user message addition $\rightarrow$ history compression $\rightarrow$ LLM turn.
- Delegates LLM streaming and the tool loop to `LLMTurnRunner`.
- Issues audit log events (`turn_start`, `turn_end`).

#### AgentContext (`agent/context.py`)

The hub for shared mutable state and component references. All services are injected via `factory.build_agent_context()`.

| Sub-structure | Scope | Key contents |
|---|---|---|
| `ctx.conv` | Session | `history`, `plan_mode`, `debug_mode`, `system_prompt_content` |
| `ctx.turn` | Per-turn | `current_turn_id` (UUID4, None between turns) |
| `ctx.stats` | Cumulative | `stat_turns`, `stat_tool_calls`, `stat_latency`, token counts |
| `ctx.workflow` | Session | `WorkflowState`: `active`, `current_task_id`, `workflow_id`, `approval_pending` (transient) |
| `ctx.cfg` | Hot-reload | `AgentConfig` (7 sub-configs) |
| `ctx.session` | Session | `AgentSession` (SQLite) |
| `ctx.services` | Injected | All service instances (LLMClient, ToolExecutor, etc.) |

#### LLMClient (`shared/llm_client.py`)

- Constructs request payloads (messages + tool_defs + temperature + max_tokens).
- SSE streaming (incremental UTF-8, heartbeat tracking).
- Reconnects upon recoverable errors.
- Detects and reports partial completions.

#### ToolExecutor (`shared/tool_executor.py`)

- MCP routing.
- Side-effect detection: serializes parallel tool calls if `write`/`delete`/`shell_run` is included.
- Resolves tool name $\rightarrow$ server key.
- Tracks health status per server.

#### HistoryManager (`agent/history.py`)

- Counts conversation history size (character count or token count).
- Triggers LLM-based summarization when thresholds are exceeded.
- Selects turns for compression (importance scoring + category).
- Protects the most recent `history_protect_turns` pair from being compressed.

#### CommandRegistry (`agent/commands/registry.py`)

Dispatches built-in commands.

#### CLIView (`agent/cli_view.py`)

- Responsible only for the presentation layer, containing no business logic.
- Provides `Writer` and `Reader` protocols for testability.
- Receives callbacks from `Orchestrator`, `HistoryManager`, and `LLMClient`.

#### LifecycleState (`agent/lifecycle.py`)

An enum representing transport state shared among lifecycle managers:

| Value | Description |
|---|---|
| `STARTING` | Server is starting |
| `RUNNING` | Server is running |
| `STOPPED` | Server is stopped |
| `FAILED` | An error occurred in the server |
| `UNKNOWN` | Initial/unknown state |

Valid transitions: `STOPPED → STARTING/FAILED`, `STARTING → RUNNING/FAILED/STOPPED`, `RUNNING → STOPPED/FAILED/STARTING`, `FAILED → STARTING/STOPPED`, `UNKNOWN → any`.

#### AgentSession (`agent/session.py`)

- CRUD for `sessions` and `messages` tables.
- Deletion/listing of RAG documents (delegated from `/db` command).
- Returns message lists for session restoration.

#### Memory Services (`agent/memory/`)

An optional subsystem enabled when `use_memory_layer=True`. Accessed via `ctx.services.memory`.

| Sub-service | Role |
|---|---|
| `injection` | Injects relevant memories at session start and each turn. |
| `ingestion` | Extracts and persists memories at session end. |
| `store` | JSONL + SQLite store for memory entries. |
| `retriever` | FTS5 and optional KNN search. |

## Key Constraints

### Shutdown

Graceful shutdown is controlled via flags. Upon receiving `SIGTERM`, the `shutdown_requested` flag is set, and the loop terminates after the next turn completion. There is a maximum 10-second grace period before timeout.

This approach was chosen to ensure the integrity of ongoing workflows rather than performing a direct system exit. Handlers do not block, instead deferring termination to the post-turn check.

Resource closing occurs after WAL checkpointing, and both calls are independent and protected. One failing does not block the other.

### Startup Validation Pipeline

Service checks accumulate results in `StartupValidationResult`, and startup is aborted if even one `FATAL` error occurs. MCP subprocesses are rolled back if an exception occurs after they have been started.

### Lifecycle Implementation Location

`LifecycleManagerProtocol` defines `ensure_ready`/`shutdown_all`/`restart`/`shutdown_idle`/`get_transport_state`/`start_http_subprocess`/`get_process_snapshot` using structural subtyping. The production implementation is in `agent/factory.py`, where HTTP subprocess startup, health polling, restart, and termination are delegated to `agent/http_lifecycle.py`.

`ensure_ready`/`start_http_subprocess`/`restart` are guarded against being ignored once shutdown has started.

## Operational Notes

- Notification and pause mechanisms when background task failure thresholds are reached are opt-in (disabled by default).
- `handle_turn()` executes the plan/execute/verify stages via the workflow engine.
  While `ctx.workflow.approval_pending` is `True`, and while background tasks are paused, new turns are rejected. (See [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md) for details.)

## Known Limitations

- Notification and pause mechanisms when background task failure thresholds are reached are opt-in (disabled by default). (See [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md) for details.)

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_02_runtime-architecture.md`

## Keywords

agent
runtime
architecture
lifecycle
