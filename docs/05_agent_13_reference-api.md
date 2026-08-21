# Agent Reference API — Part 1

## Purpose

A concise per-module API reference including roles, primary public APIs, callers, callees, relevant configurations, and failure behavior. For full method signatures, refer to the respective chapters linked below.

> **Scope of this chapter:** Function signatures, parameter types, return values, error conditions.
> For component context, data flow, and runtime behavior → see [05_agent_02 Runtime Architecture](05_agent_02_runtime-architecture.md).

## Design Intent

The API reference focuses on "what the API is" and "how it works." "Why this API was designed this way" is within the scope of design documentation.

## Responsibility Boundary

- **Owned by this file:** Function signatures, parameter types, return values, error conditions.
- **Not owned by this file:** Component context, data flow, runtime behavior.

## Key Constraints

- Detailed API references exist only in the Canonical Source defined by the Canonical Source Rule.
- Duplication of API/type/method details in other chapters is prohibited (Canonical Source Rule).
- Incomplete implementation changes must be explicitly marked with a `Needs Confirmation` flag.

## Operational Notes

- Calls from the REPL loop driver are always in `await` format.
- Different fallback behaviors exist for different error types upon failure.
- The memory layer is optional and designed to be safely guarded when `ctx.services.memory is None`.

## Known Limitations

- Some callees involve indirect dependencies (e.g., `factory.build_agent_context()` is called via `StartupOrchestrator`).
- Differences between legacy documentation and current code are explicitly marked with `Needs Confirmation` flags.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_13_reference-api.md`

---

## AgentREPL (`agent/repl.py`)

- **Role:** REPL coordinator. A thin startup/loop driver.
- **Primary API:** `await AgentREPL().run()`
- **Caller:** `agent/__main__.py`
- **Callees:** `agent/startup.StartupOrchestrator` (constructed and executed within `run()`, receiving `CommandRegistry` and `Orchestrator`), `CLIView`
- **Configuration:** Entire `AgentConfig`
- **On Failure:** Unhandled exceptions propagate to the event loop. `finally` always closes resources.

Full details: [05_agent_02_runtime-architecture.md AgentREPL](05_agent_02_runtime-architecture.md)

---

## Orchestrator (`agent/orchestrator.py`)

- **Role:** Turn-level facade. Manages memory injection → compression → LLM → tool loop.
- **Primary API:** `await Orchestrator.handle_turn(line)`, `workflow_status() -> dict[str, str]`
- **Caller:** REPL loop driver
- **Callees:** `LLMTurnRunner`, `HistoryManager` (`ctx.services_required.hist_mgr.compress()`), `AgentSession`, `MemoryServices` (`ctx.services_required.memory.on_user_prompt()`), `WorkflowEngine` / `StateStore` / `WorkflowLoader` (`agent/workflow/`), `ToolLoopGuard`
- **Configuration:** `cfg.llm.*`, `cfg.tool.*`, `cfg.memory.*`
- **On Failure:** `LLMTransportError` is caught internally; REPL continues. If `WorkflowLoader().load()` fails during `__init__()`, a `RuntimeError` is raised, causing construction of the `Orchestrator` itself to fail (workflow definitions are mandatory).

Full details: [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)

---

## AgentContext (`agent/context.py`)

- **Role:** Session-specific DI hub. A container for shared mutable state.
- **Primary API:** `ctx.conv`, `ctx.turn`, `ctx.stats`, `ctx.workflow`, `ctx.cfg`, `ctx.session`, `ctx.services`, `ctx.diagnostics`, `ctx.services_required`
- **Caller:** All components
- **Callee:** None (pure state holder class)
- **Configuration:** `AgentConfig` is held as `ctx.cfg`
- **On Failure:** The `ctx.services_required` property raises a `RuntimeError` if `ctx.services` is `None` (before `factory.build_agent_context()` completes). Direct access to `ctx.services` itself does not fail (it merely returns `None`).

Full details: [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)

---

## LLMClient (`shared/llm_client.py`)

- **Role:** HTTP communication with LLM. SSE streaming + retries.
- **Primary API:** `await client.stream(url, history, tool_defs)`, `client.build_payload(...)`
- **Caller:** `LLMTurnRunner`, `HistoryManager` (via `call()`), `SessionTitleService`
- **Callee:** `RobustSSEParser`, `httpx.AsyncClient`
- **Configuration:** `cfg.llm.*`
- **On Failure:** Raises `LLMTransportError` with `partial_text` upon stream failure.

Full details: [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md)

---

## ToolExecutor (`shared/tool_executor.py`)

- **Role:** MCP tool routing with TTL cache, side-effect classification, and concurrency limits.
- **Primary API:** `await executor.execute(tool_name, args) -> ToolCallResult`
- **Caller:** `LLMTurnRunner` (via `execute_all_tool_calls`)
- **Callee:** `ToolRouteResolver`, `HttpTransport`, `McpServerHealthRegistry`
- **Configuration:** `cfg.tool.*`, `cfg.mcp.*`
- **On Failure:** Returns `ToolCallResult(is_error=True)` upon transport failure.

Full details: [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md)

---

## ToolRouteResolver (`shared/route_resolver.py`) — Internal component of ToolExecutor

- **Role:** Acts as the **sole routing authority** using `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`, built via live `/v1/tools` discovery by `McpToolDiscoveryService`) to resolve `tool_name → server_key`.
- **Primary API:** `resolve(tool_name) -> server_key`
- **Caller:** Tool execution layer (`ToolExecutor._raw_execute`)
- **Callee:** None (only references `RuntimeToolRegistry` instance. Does not touch `ToolRegistry`).
- **Configuration:** No direct configuration. The constructor accepts `server_configs` for backward compatibility but does not read them.
- **On Failure:** If the tool name is not found in the registry, a `ValueError` is raised immediately without fallback.

> **Evidence Classification: Explicit in code (Correction).** Previous versions described a "4-layer cascade (live discovery > ToolRegistry > config `tool_names` > static constants)" and stated that a `KeyError` would occur on failure. However, after `shared/route_resolver.py::ToolRouteResolver.resolve()` was updated to only reference `ToolRegistry` and raise `ValueError` if no match is found, and subsequently migrated to `RuntimeToolRegistry` (`shared/runtime_tool_registry.py`), the logic changed. `ToolRegistry` has been downgraded to seed data for drift detection and is no longer used for routing decisions. Config `tool_names` is merely drift verification metadata and not an input for routing. This change follows the implementation in `04_mcp_03_01_dispatch-and-routing.md` Reliable source of routing information.

Full details: [04_mcp_03_01_dispatch-and-routing.md Reliable source of routing information](04_mcp_03_01_dispatch-and-routing.md)

---

# Agent Reference API — Part 2

## Purpose

A concise per-module API reference including roles, primary public APIs, callers, callees, relevant configurations, and failure behavior. For full method signatures, refer to the respective chapters linked below.

## Design Intent

The API reference focuses on "what the API is" and "how it works." "Why this API was designed this way" is within the scope of design documentation.

## Responsibility Boundary

- **Owned by this file:** Function signatures, parameter types, return values, error conditions.
- **Not owned by this file:** Component context, data flow, runtime behavior.

## Key Constraints

- Detailed API references exist only in the Canonical Source defined by the Canonical Source Rule.
- Duplication of API/type/method details in other chapters is prohibited (Canonical Source Rule).
- Incomplete implementation changes must be explicitly marked with a `Needs Confirmation` flag.

## Operational Notes

- REPL loop driver calls are always in `await` format.
- Different fallback behaviors exist for different error types upon failure.
- The memory layer is optional and designed to be safely guarded when `ctx.services.memory is None`.

## Known Limitations

- Some callees involve indirect dependencies.
- Differences between legacy documentation and current code are explicitly marked with `Needs Confirmation` flags.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_13_reference-api.md`

---

## HistoryManager (`agent/history.py`)

- **Role:** Conversation history size management and LLM-based compression.
- **Primary API:** `await mgr.compress(history)`, `await mgr.force_compress(history)`, `mgr.count_chars(history)`, `mgr.count_tokens(history, last_input_tokens=None)`, `await mgr.count_tokens_async(...)`, `apply_config(...)`
- **Caller:** Orchestrator's history compression process, `/compact` command (`force_compress`)
- **Callee:** `httpx.AsyncClient` (injected via constructor `http`; summary LLM calls use `self._http.post()` directly instead of going through `shared/llm_client.py::LLMClient`), `HistorySelectionPolicy`
- **Configuration:** `cfg.llm.context_char_limit`, `context_compress_turns`, `history_protect_turns`
- **On Failure:** If LLM summarization fails (`HistoryCompressionError`) → If character limit exceeded, fall back to truncation starting from least important messages. If only token limit exceeded, return history unchanged.

> **Evidence Classification: Explicit in code (Correction).** Previous versions stated that callees were `LLMClient`, but summary LLM calls actually perform direct `self._http.post()` requests against the `httpx.AsyncClient` provided at construction, bypassing the `shared/llm_client.py::LLMClient` instance. Additionally, the description "no compression on failure" was incomplete; if character limits are exceeded, fallback truncation occurs (`stat_fallback_truncate_count` is incremented). If only token limits are exceeded, the history is returned unchanged.

Full details: [05_agent_04_01_state-and-persistence-state-model.md HistoryManager](05_agent_04_01_state-and-persistence-state-model.md)

---

## CommandRegistry (`agent/commands/registry.py`)

- **Role:** Dispatcher for all slash commands. 15 mixin-based command groups.
- **Primary API:** `await cmds.dispatch(line) -> bool`
- **Caller:** REPL loop driver
- **Callee:** 15 mixin handlers + plugin registry
- **Configuration:** Different `cfg.*` fields per command
- **On Failure:** Command errors are displayed to the user. REPL continues.

Full details: [05_agent_07_01_cli-and-commands-cli-reference.md](05_agent_07_01_cli-and-commands-cli-reference.md)

---

## CLIView (`agent/cli_view.py`)

- **Role:** CLI presentation layer. Readline, progress display, multi-line input.
- **Primary API:** `setup_readline()`, `write_token()`, `write_progress()`, `async read_multiline()`
- **Caller:** `AgentREPL`, `Orchestrator` (via Writer protocol callback)
- **Callee:** `readline`, `sys.stdout`
- **Configuration:** No direct configuration. Callbacks are wired during construction.
- **On Failure:** I/O errors propagate to the caller.

Full details: [05_agent_07_01_cli-and-commands-cli-reference.md CLIView](05_agent_07_01_cli-and-commands-cli-reference.md)

---

## AgentSession (`agent/session.py`)

- **Role:** Persistence of sessions and messages to SQLite (RAG document operations have been migrated to rag-pipeline-mcp).
- **Primary API:** `start()`, `save(role, content)`, `save_diagnostic(content)`, `fetch_messages(session_id)`
- **Skip Counters:** `skipped_no_session_count`, `skipped_invalid_role_count` (read-only properties per session)
- **Strict Mode:** `AgentSession(strict_mode=True)` raises a `RuntimeError` on the first skipped save instead of warning.
- **Caller:** `Orchestrator`, `CommandRegistry` (`/session` command; `/db` command is delegated to rag-pipeline-mcp)
- **Callee:** `SQLiteHelper`
- **Configuration:** DB path is retrieved from `config/agent.toml`
- **On Failure:** Fatal failures result in `sqlite3.Error`. If `session_id=None`, a warning is logged and the counter is incremented.

Full details: [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

---

## AgentConfig (`agent/config_dataclasses.py`)

- **Role:** Configuration container. 7 sub-configurations. Supports hot-reloading via `/reload`.
- **Primary API:** `build_agent_config(cfg_override=None) -> AgentConfig`
- **Caller:** Session initialization, config reloading
- **Callee:** `ConfigLoader.load_all()`
- **Configuration:** `config/agent.toml`
- **On Failure:** `ConfigLoadError` on file read/parse failure.

Full details: [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md)

---

## MemoryServices (`agent/memory/`)

- **Role:** Optional persistent semantic memory subsystem.
- **Primary API:** `memory.on_session_start()`, `memory.on_user_prompt(query, session_id)`, `memory.on_session_stop()`
- **Caller:** `Orchestrator`, `AgentREPL` (at startup/shutdown)
- **Callee:** `MemoryStore`, `MemoryRetriever`, `EmbeddingClient`
- **Configuration:** `cfg.memory.*`
- **On Failure:** Errors are logged. REPL continues without memory (graceful degradation).

**Activation:** If `use_memory_layer=True` (default), `ctx.services.memory` becomes active.
Always null-check before accessing memory services.
