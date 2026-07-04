# Agent Reference API

- Document guide → [05_agent_00_document-guide.md](05_agent_00_document-guide.md)

## Purpose

Concise per-module API reference with role, primary public APIs, callers, callees,
related configuration, and failure behavior. For full method signatures see linked chapters.

> **Scope of this chapter:** function signatures, parameter types, return values, and error conditions.
> For component context, data flow, and runtime behavior → [05_agent_02 §Runtime Architecture](05_agent_02_runtime-architecture.md).

---

## AgentREPL (`agent/repl.py`)

- **Role:** REPL coordinator; thin startup/loop driver
- **Primary API:** `await AgentREPL().run()`
- **Callers:** `agent/__main__.py`
- **Callees:** `Orchestrator`, `CommandRegistry`, `CLIView`, `factory.build_agent_context()`
- **Config:** all of `AgentConfig`
- **Failure:** unhandled exceptions propagate to event loop; `finally` always closes resources

Full details: [05_agent_02_runtime-architecture.md §AgentREPL](05_agent_02_runtime-architecture.md)

---

## Orchestrator (`agent/orchestrator.py`)

- **Role:** Turn-level facade; owns memory injection → compress → LLM → tool loop
- **Primary API:** `await Orchestrator.handle_turn(line)`
- **Callers:** REPL loop driver
- **Callees:** `LLMTurnRunner`, `HistoryManager`, `AgentSession`, `MemoryInjectionService`
- **Config:** `cfg.llm.*`, `cfg.tool.*`, `cfg.memory.*`
- **Failure:** `LLMTransportError` caught internally; REPL continues

Full details: [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md)

---

## AgentContext (`agent/context.py`)

- **Role:** Per-session DI hub; shared mutable state container
- **Primary API:** `ctx.conv`, `ctx.turn`, `ctx.stats`, `ctx.cfg`, `ctx.session`, `ctx.services`
- **Callers:** all components
- **Callees:** none (pure state holder)
- **Config:** `AgentConfig` stored as `ctx.cfg`
- **Failure:** N/A

Full details: [05_agent_04_state-and-persistence.md](05_agent_04_state-and-persistence.md)

---

## LLMClient (`shared/llm_client.py`)

- **Role:** LLM HTTP communication; SSE streaming + retry
- **Primary API:** `await client.stream(url, history, tool_defs)`, `client.build_payload(...)`
- **Callers:** `LLMTurnRunner`, `HistoryManager` (via `call()`), `SessionTitleService`
- **Callees:** `RobustSSEParser`, `httpx.AsyncClient`
- **Config:** `cfg.llm.*`
- **Failure:** raises `LLMTransportError` with `partial_text` on stream failure

Full details: [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md)

---

## ToolExecutor (`shared/tool_executor.py`)

- **Role:** MCP tool routing with TTL cache, side-effect classification, concurrency limits
- **Primary API:** `await executor.execute(tool_name, args) -> ToolCallResult`
- **Callers:** `LLMTurnRunner` (via `execute_all_tool_calls`)
- **Callees:** `ToolRouteResolver`, `HttpTransport`, `StdioTransport`, `McpServerHealthRegistry`
- **Config:** `cfg.tool.*`, `cfg.mcp.*`
- **Failure:** returns `ToolCallResult(is_error=True)` on transport failure

Full details: [05_agent_06_tool-execution-and-approval.md](05_agent_06_tool-execution-and-approval.md)

---

## ToolRouteResolver (`shared/route_resolver.py`) — internal component of ToolExecutor

- **Role:** Four-layer tool-to-server routing cascade (live discovery > ToolRegistry > config `tool_names` > static constants)
- **Primary API:** `resolve(tool_name) -> server_key`
- **Callers:** Tool execution layer
- **Callees:** `McpServerHealthRegistry`, `LifecycleProtocol` (via server startup)
- **Config:** None directly; reads from ToolRegistry, live discovery map, config `tool_names`, and `tool_constants.py` frozensets in priority order
- **Failure:** raises `KeyError` if no layer resolves the tool name

Full details: [04_mcp_03 §Routing Source of Truth](04_mcp_03_routing_lifecycle_and_execution.md#routing-source-of-truth)

---

## HistoryManager (`agent/history.py`)

- **Role:** Conversation history size management and LLM-based compression
- **Primary API:** `await mgr.compress(history)`, `mgr.count_chars(history)`, `apply_config(...)`
- **Callers:** Orchestrator history compression
- **Callees:** `LLMClient`, `HistorySelectionPolicy`
- **Config:** `cfg.llm.context_char_limit`, `context_compress_turns`, `history_protect_turns`
- **Failure:** LLM summarization failure → returns unmodified history (no compression)

Full details: [05_agent_04_state-and-persistence.md §HistoryManager](05_agent_04_state-and-persistence.md)

---

## CommandRegistry (`agent/commands/registry.py`)

- **Role:** All slash command dispatch; 13 mixin-based command groups
- **Primary API:** `await cmds.dispatch(line) -> bool`
- **Callers:** REPL loop driver
- **Callees:** 10 mixin handlers + plugin registry
- **Config:** various `cfg.*` fields per command
- **Failure:** command errors displayed to user; REPL continues

Full details: [05_agent_07_cli-and-commands.md](05_agent_07_cli-and-commands.md)

---

## CLIView (`agent/cli_view.py`)

- **Role:** CLI presentation layer; readline, progress, multiline input
- **Primary API:** `setup_readline()`, `write_token()`, `write_progress()`, `async read_multiline()`
- **Callers:** `AgentREPL`, `Orchestrator` (via Writer protocol callbacks)
- **Callees:** `readline`, `sys.stdout`
- **Config:** none directly; callbacks wired at construction
- **Failure:** I/O errors propagate to caller

Full details: [05_agent_07_cli-and-commands.md §CLIView](05_agent_07_cli-and-commands.md)

---

## AgentSession (`agent/session.py`)

- **Role:** SQLite persistence for sessions and messages (RAG document ops moved to rag-pipeline-mcp)
- **Primary API:** `start()`, `save(role, content)`, `save_diagnostic(content)`, `fetch_messages(session_id)`
- **Skip counters:** `skipped_no_session_count`, `skipped_invalid_role_count` (per-session, read-only properties)
- **Strict mode:** `AgentSession(strict_mode=True)` raises `RuntimeError` on first skipped save instead of warning
- **Callers:** `Orchestrator`, `CommandRegistry` (`/session` commands; `/db` commands delegate to rag-pipeline-mcp)
- **Callees:** `SQLiteHelper`
- **Config:** DB path from `config/common.toml`
- **Failure:** `sqlite3.Error` on critical failures; logs warning and increments counter on `session_id=None`

Full details: [05_agent_09_data-layer.md](05_agent_09_data-layer.md)

---

## AgentConfig (`agent/config_dataclasses.py`)

- **Role:** Configuration container; 7 sub-configs; hot-reloadable via `/reload`
- **Primary API:** `build_agent_config(cfg_override=None) -> AgentConfig`
- **Callers:** Session initialization, config reload
- **Callees:** `ConfigLoader.load_all()`
- **Config:** all TOML files in `config/`
- **Failure:** `ConfigLoadError` on file read/parse failure

Full details: [05_agent_08_configuration.md](05_agent_08_configuration.md)

---

## _ServerLifecycleRouter (`factory.py`)

- **Role:** HTTP subprocess + stdio server lifecycle management
- **Primary API:** `ensure_ready(server_key)`, `shutdown_all()`, `restart(server_key)`
- **Callers:** MCP server startup, tool execution layer, watchdog loop
- **Callees:** `StdioTransport`, `HttpTransport`, uvicorn subprocess
- **Config:** `cfg.mcp.mcp_servers`, `cfg.mcp.mcp_watchdog_interval`
- **Failure:** `RuntimeError` on subprocess startup timeout

**Note:** `ServerLifecycleManager` was deleted. Only `restart_stdio()` remains in
`agent/lifecycle.py`. All other lifecycle functions are in `_ServerLifecycleRouter`.

Full details: [04_mcp_03_routing_lifecycle_and_execution.md](04_mcp_03_routing_lifecycle_and_execution.md)

---

## MemoryServices (`agent/memory/`)

- **Role:** Optional persistent semantic memory subsystem
- **Primary API:** `memory.on_session_start()`, `memory.on_user_prompt(query, session_id)`, `memory.on_session_stop()`
- **Callers:** `Orchestrator`, `AgentREPL` (startup/shutdown)
- **Callees:** `MemoryStore`, `MemoryRetriever`, `EmbeddingClient`
- **Config:** `cfg.memory.*`
- **Failure:** errors logged; REPL continues without memory (graceful degradation)

**Activation:** `ctx.services.memory` is `None` when `use_memory_layer=False` (default).
Always null-check before accessing memory services.
