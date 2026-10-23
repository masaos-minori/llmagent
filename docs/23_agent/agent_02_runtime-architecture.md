---
title: "Agent Runtime Architecture"
area: agent
tags:
  - agent
  - runtime
  - architecture
related:
  - agent_01_system-overview.md
  - agent_00_document-guide.md
  - agent_11_01_memory-overview-and-modes.md
  - agent_12_reference-api.md
  - agent_03_01_turn-processing-flow-overview.md
---
# Agent Runtime Architecture

## Purpose

Describes the primary runtime components, their dependencies, and responsibility boundaries, enabling engineers and AI to identify where specific behaviors are implemented.

> **Scope of this chapter:** Runtime behavior, module graph, data flow, and component lifecycles. For function signatures, parameter types, and return values → see [agent_12 Reference API](agent_12_reference-api.md).

## Responsibility Boundary

### Component Responsibilities

- **Component Responsibilities**: see Runtime Extension Points, Lifecycle and Shutdown below (one entry per component).
- **Owned State**: AgentREPL owns the input loop and UI state; AgentContext owns shared mutable state and component references; each service owns its own runtime state.
- **Allowed Dependency Direction**: AgentREPL depends on StartupOrchestrator, AgentContext, CLIView, Orchestrator; Orchestrator depends on LlmTurnExecutor; AgentContext depends on LLMClient, ToolExecutor, HistoryManager, ServerLifecycleRouter; no circular dependencies among services.
- **Reason for Process Separation**: Decoupling StartupOrchestrator from AgentREPL allows complexity during startup (service checks, MCP server startup) to be separated from REPL's responsibility, so the REPL focuses solely on UI concerns; decoupling Orchestrator from LlmTurnExecutor separates turn-level coordination from LLM streaming and tool loop execution.
- **Design Boundaries Requiring Joint Review**: Architecture decisions affecting multiple subsystems require joint review; cross-component state transitions require coordinated testing when any component's contract changes.

### Responsibility Boundary Supplement

- `AgentContext` and `Orchestrator` details → see the AgentContext and Orchestrator entries under Runtime Extension Points, Lifecycle and Shutdown below.
- Lifecycle implementation → see Lifecycle Implementation below.

## Key Constraints

- Workflow definition load failure in `Orchestrator.__init__()` raises `RuntimeError` and stops startup.
- Parallel/serial determination of tool calls is made by the scheduler, not by `ToolExecutor`; the rules are canonical in [agent_06_01](agent_06_01_tool-execution-and-approval-execution.md). Each serialization is logged as `ROUND_SERIALIZATION` with a reason (Explicit in code — `scripts/agent/tool_scheduler.py`).

## Operational Notes

- `AgentContext.diagnostics` is `None` until `Orchestrator.__init__()` assigns the `DiagnosticStore`.
- `handle_turn()` executes the plan/execute/verify stages via the workflow engine. New turns are rejected while background tasks are paused. (See [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md) for details.)

## Known Limitations

- Notification and pause mechanisms when background task failure thresholds are reached are opt-in (disabled by default). (See [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md) for details.)

## Preflight Gate Coverage

Every non-READ execution path must pass `check_preflight()` before a tool is executed. Because an untested path may bypass the gate, any new path requires a test or a documented exemption.

### Enforcement Points

- `RepositoryGateway.execute()` (`scripts/agent/repository_gateway.py`): the primary gate for write/delete/API-write operations.
- `check_approval()` in `scripts/agent/tool_approval.py`: runs preflight before the approval decision.
- `execute_one_tool_call()` in `scripts/agent/tool_runner.py`: when no gateway is configured (not expected in production, where `RepositoryGateway` is created unconditionally), non-READ operations still run `check_preflight()` before `tools.execute()`.

### Exempt Paths

- READ operations pass through the gateway without preflight: read-only tools are exempt by design.
- The dry-run preview executed by tool-level approval is exempt: it is a read-only operation with no separate preview method.

### Maintenance Rule

Standardizing all write/delete/API-write operations through the gateway is the target model. A change to gate placement must update this section as part of its acceptance criteria.

## Runtime Extension Points, Lifecycle and Shutdown


### Purpose

Describes runtime extension points, lifecycle phases, and shutdown policies, clarifying component operation duration and interdependencies.

### Design Intent

`AgentREPL` is responsible only for the UI loop, command dispatching, and output display, containing no business logic. By delegating all startup sequences to `StartupOrchestrator`, the REPL functions purely as an I/O layer.

### Responsibility Boundary

#### Component Responsibilities

##### AgentREPL (`agent/repl.py`)

- Manages the input/dispatch loop: reads lines → commands or LLM turns.
- Manages graceful shutdown.
- Contains no business logic. Responsible only for UI loop, command dispatch, and output display.

##### StartupOrchestrator (`agent/startup.py`)

- Encapsulates all startup orchestration processes extracted from `AgentREPL`.
- Decouples startup complexity so that `AgentREPL` remains focused on UI concerns.

##### Orchestrator (`agent/orchestrator.py`)

- Handles end-to-end processing of a single user turn.
- Manages the flow: memory injection → user message addition → history compression → LLM turn.
- Delegates LLM streaming and the tool loop to `LlmTurnExecutor`.
- Issues audit log events (`turn_start`, `turn_end`).

##### AgentContext (`agent/context.py`)

The hub for shared mutable state and component references. All services are injected via `factory.build_agent_context()`. State is grouped by lifetime: session-scoped conversation state (`ctx.conv`, including history, plan mode and debug mode), per-turn state (`ctx.turn`, whose turn ID is `None` between turns), cumulative runtime statistics (`ctx.stats`), transient workflow state (`ctx.workflow`), hot-reloadable configuration (`ctx.cfg`), the session handle (`ctx.session`), and the injected service instances (`ctx.services`). Persistence and scope semantics of this state: [agent_04_01](agent_04_01_state-and-persistence-state-model.md) and [agent_04_02](agent_04_02_state-and-persistence-history-compression.md); field definitions: `scripts/agent/context.py`.

##### LLMClient (`shared/llm_client.py`)

- Constructs request payloads (messages + tool_defs + temperature + max_tokens).
- SSE streaming (incremental UTF-8, heartbeat tracking).
- Reconnects upon recoverable errors.
- Detects and reports partial completions.

##### ToolExecutor (`shared/tool_executor.py`)

- MCP routing.
- MCP call dispatch only; parallel/serial scheduling is decided by the scheduler (see Key Constraints).
- Resolves tool name → server key.
- Tracks health status per server.

##### HistoryManager (`agent/history.py`)

- Counts conversation history size (character count or token count).
- Triggers LLM-based summarization when thresholds are exceeded.
- Selects turns for compression (importance scoring + category).
- Protects the most recent `history_protect_turns` pair from being compressed.

##### CommandRegistry (`agent/commands/registry.py`)

Dispatches built-in commands.

##### CLIView (`agent/cli_view.py`)

- Responsible only for the presentation layer, containing no business logic.
- Provides `Writer` and `Reader` protocols for testability.
- Receives callbacks from `Orchestrator`, `HistoryManager`, and `LLMClient`.

##### LifecycleState (`agent/lifecycle.py`)

An enum representing transport state (`STARTING`, `RUNNING`, `STOPPED`, `FAILED`, `UNKNOWN`) shared among lifecycle managers.

Valid transitions: `STOPPED → STARTING/FAILED`, `STARTING → RUNNING/FAILED/STOPPED`, `RUNNING → STOPPED/FAILED/STARTING`, `FAILED → STARTING/STOPPED`, `UNKNOWN → any`.

##### AgentSession (`agent/session.py`)

- CRUD for `sessions` and `messages` tables.
- Deletion/listing of RAG documents is not handled here; it goes through `rag-pipeline-mcp`.
- Returns message lists for session restoration.

##### Memory Services (`agent/memory/`)

An optional subsystem enabled when `use_memory_layer=True`, accessed via `ctx.services.memory`. It injects relevant memories at session start and on each user prompt (see [agent_11_01](agent_11_01_memory-overview-and-modes.md)), extracts and persists memories at session end, and stores them in JSONL plus SQLite with FTS5 and optional KNN retrieval.

##### EventBus Client Modules (`agent/eventbus_client.py`, `agent/eventbus_subscriber.py`, `agent/eventbus_topic_admin_client.py`)

Client-side libraries for the Event Bus HTTP API: `EventBusClient` publishes events, `EventBusSubscriber` consumes the `/subscribe` SSE stream (reconnecting with a fresh `consumer_id`), and `EventBusTopicAdminClient` updates the admin topics-authorization settings. No runtime component of the Agent process imports these modules; only their unit tests do, so the Agent does not currently publish to or subscribe from the Event Bus by itself.

### Key Constraints

#### Shutdown

Graceful shutdown is controlled via flags. On a signal, the `shutdown_requested` flag and the shared shutdown event are set. At the prompt this ends the loop immediately (`TestSignalDuringPromptEndsLoop`); during a turn the in-flight dispatch is cancelled and the wait for that cancellation is bounded by `_GRACEFUL_TIMEOUT_S` before the loop exits (`TestMidTurnSignalIsBounded`).

The bound keeps a slow or non-cooperative turn from hanging the loop indefinitely, rather than performing a direct system exit. Handlers do not block; the loop stops waiting for the cancelled dispatch once the bound elapses.

Resource closing occurs after WAL checkpointing, and both calls are independent and protected. One failing does not block the other.

#### Startup Validation Pipeline

Service checks accumulate results in `StartupValidationResult`, and startup is aborted if even one `FATAL` error occurs. MCP subprocesses are rolled back if an exception occurs after they have been started.

#### Lifecycle Implementation

`LifecycleManagerProtocol` (structural subtyping) is the lifecycle contract. The production implementation is `_ServerLifecycleRouter` in `agent/lifecycle_router.py` (constructed by `agent/factory.py`); HTTP subprocess startup, health polling, restart, and termination are delegated to `agent/http_lifecycle.py`.

`ensure_ready`/`start_http_subprocess`/`restart` are guarded against being ignored once shutdown has started.

## Keywords

- agent
- runtime
- architecture
- lifecycle
