# Agent Inconsistencies and Known Issues

This file catalogs known bugs, spec conflicts, document inconsistencies, unimplemented
areas, and open questions in the agent layer (`agent/`, `shared/`).

Each entry format:
- **Type:** `Document inconsistency` / `Implementation bug` / `Undocumented` / `Needs confirmation` / `Open Question`
- **Impact scope:** Affected modules / behavior
- **Statement A / B:** Conflicting facts (when applicable)
- **Current safe interpretation:** What to assume when uncertain
- **Recommended action:** Fix or investigation needed
- **Notes for AI reference:** Guidance for AI reasoning about this issue

---

## Document Inconsistencies

### DOC-01: `repl_tool_exec.py` was deleted — do not reference

- **Type:** Document inconsistency (resolved)
- **Impact scope:** Any code or doc referencing `agent/repl_tool_exec.py`
- **Statement A:** Older source docs (`05_agent-impl-class.md`, `05_ref-agent-repl.md`) described `repl_tool_exec.py` as containing tool approval/execution logic.
- **Statement B:** `repl_tool_exec.py` was deleted. All tool approval and execution logic was consolidated into `shared/tool_executor.py` (`ToolExecutor`).
- **Current safe interpretation:** `agent/repl_tool_exec.py` does not exist. Use `ToolExecutor.execute()` in `shared/tool_executor.py` for all tool dispatch.
- **Recommended action:** Any remaining references to `repl_tool_exec.py` in code or docs must be removed.
- **Notes for AI reference:** `ToolExecutor` in `shared/tool_executor.py` is the single authoritative tool execution entry point. See `05_agent_06_tool-execution-and-approval.md`.

---

### DOC-02: `ServerLifecycleManager` was deleted from `agent/lifecycle.py`

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `agent/lifecycle.py`, `factory.py`, any code referencing `ServerLifecycleManager`
- **Statement A:** Older specs described `ServerLifecycleManager` as owning HTTP subprocess and stdio server lifecycle (start/stop/restart/ensure_ready/shutdown_all).
- **Statement B:** `ServerLifecycleManager` was deleted. Lifecycle routing moved to `_ServerLifecycleRouter` in `factory.py`. Only `restart_stdio()` remains in `agent/lifecycle.py`.
- **Current safe interpretation:** Use `_ServerLifecycleRouter` for all lifecycle operations. Do not import or instantiate `ServerLifecycleManager`.
- **Recommended action:** Verify no remaining imports of `ServerLifecycleManager` exist.
- **Notes for AI reference:** `_ServerLifecycleRouter` (private class in `factory.py`) is the canonical lifecycle coordinator. It implements `LifecycleProtocol` and is injected into `ToolExecutor` via `set_lifecycle()`.

---

### DOC-03: `MCPConfig.github_url` field name differs from `github_server_url` config key

- **Type:** Document inconsistency / Needs confirmation
- **Impact scope:** `shared/mcp_config.py MCPConfig`, `config/agent.toml`, `agent/config.py build_agent_config()`
- **Statement A:** The `MCPConfig` dataclass field is named `github_url`.
- **Statement B:** The configuration file (`config/agent.toml`) and `build_agent_config()` read this value via the key `github_server_url` (not `github_url`).
- **Current safe interpretation:** In `config/agent.toml`, use `github_server_url = "http://127.0.0.1:8006"`. Do not use `github_url` as a config key.
- **Recommended action:** Align the dataclass field name to `github_server_url` for clarity, or document the mapping explicitly in `MCPConfig`.
- **Notes for AI reference:** `build_agent_config()` calls `cfg.get("github_server_url", "http://127.0.0.1:8006")` to populate `MCPConfig.github_url`. The dataclass field name and the TOML key are different.

---

### DOC-04: `05_agent_00` Known Limitations references deleted file `05_ref-agent-context.md`

- **Type:** Document inconsistency (stale reference)
- **Impact scope:** `docs/05_agent_00_document-guide.md §Known Limitations`
- **Statement A:** `05_agent_00_document-guide.md` states: "Memory layer documentation (agent/memory/) is summarized only; detailed API is in `docs/05_ref-agent-context.md` (retained source file)."
- **Statement B:** `docs/05_ref-agent-context.md` was deleted as part of the documentation restructuring.
- **Current safe interpretation:** Memory layer API is summarized in `05_agent_02_runtime-architecture.md §Memory Services` and `05_agent_04_state-and-persistence.md`. No separate detailed reference exists.
- **Recommended action:** Update the Known Limitations section in `05_agent_00_document-guide.md` to remove the stale reference.
- **Notes for AI reference:** Do not look for `05_ref-agent-context.md` — it no longer exists.

---

### DOC-05: Budget breakdown category count — 4 vs 3

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `agent/services/context_view.py budget_breakdown()`, `/context` command output
- **Statement A:** Older source doc (`05_agent-impl-flow.md §3.3`) described 4 budget categories: `system`, `rag`, `history`, `tool_results`.
- **Statement B:** Current implementation (confirmed in `05_ref-agent-commands.md`, now deleted) shows `budget_breakdown()` returns `ContextBudget(system, history, tool_results)` — 3 categories. The `rag` category was removed or merged into `system`.
- **Current safe interpretation:** `/context` shows 3 budget categories: `system`, `history`, `tool_results`. No separate `rag` category exists.
- **Recommended action:** No action needed (already resolved). Note for AI: do not expect a `rag` field in `ContextBudget`.
- **Notes for AI reference:** `ContextBudget` has exactly 3 fields. `budget_breakdown()` is in `agent/services/context_view.py`.

---

## Implementation Bugs

### BUG-01 (cross-reference): `McpServerHealthRegistry` state never transitions

- **Type:** Implementation bug
- **Impact scope:** `shared/tool_executor.py ToolExecutor._raw_execute()`, `shared/mcp_config.py McpServerHealthRegistry`
- **Description:** `ToolExecutor._raw_execute()` checks `is_unavailable()` and blocks dispatch when UNAVAILABLE, but never calls `record_failure()` on transport error or `record_success()` on success. The HEALTHY→DEGRADED→UNAVAILABLE transition never occurs in practice. See full details in [`04_mcp_90_inconsistencies_and_known_issues.md §BUG-01`](04_mcp_90_inconsistencies_and_known_issues.md).
- **Current safe interpretation:** `McpServerHealthRegistry` always returns HEALTHY. The `is_unavailable()` check in `_raw_execute()` is effectively dead code. Degraded MCP servers will not be blocked from dispatch.
- **Recommended action:** Add `record_failure()` after transport errors and `record_success()` after successful responses in `_raw_execute()`. See `tool_executor.py:509-516`.
- **Notes for AI reference:** Do not rely on `McpServerHealthRegistry` to detect or isolate failing MCP servers. Use `/mcp` health probes or log monitoring instead.

---

## Open Questions

### OQ-01: `AgentSession` owns RAG-layer table access — responsibility boundary unclear

- **Type:** Open Question / Needs confirmation
- **Impact scope:** `agent/session.py AgentSession`, `/db clean`, `/db stats` commands, `RAG` layer
- **Description:** `AgentSession` (`agent/session.py`) implements `delete_document(url)` and `list_documents()`, which directly access the RAG layer tables (`documents`, `chunks`, `chunks_vec`) in `rag.sqlite`. This makes the agent layer depend on the RAG schema.
- **Current safe interpretation:** The current implementation works. `AgentSession` accesses RAG tables for `/db clean` and `/db stats` as a convenience. This is a known responsibility boundary violation.
- **Recommended action:** Consider moving RAG document management to `rag-pipeline-mcp` and having agent commands call it via MCP. Track before any RAG layer schema refactoring.
- **Notes for AI reference:** When modifying `AgentSession`, be aware it contains both session-layer and RAG-layer operations. Do not assume `agent/session.py` touches only `session.sqlite`.

---

### OQ-02: WorkflowEngine fallback trigger conditions are not fully specified

- **Type:** Open Question / Needs confirmation
- **Impact scope:** `agent/workflow/`, `agent/orchestrator.py Orchestrator.handle_turn()`
- **Description:** `Orchestrator.handle_turn()` uses `WorkflowEngine` when `config/workflows/default.json` exists AND `workflow.sqlite` is available. Falls back to direct execution otherwise. The exact exception types that trigger fallback (vs. hard failure), and whether partial `workflow.sqlite` state is cleaned up on fallback, are not documented.
- **Current safe interpretation:** If `config/workflows/default.json` is absent or `workflow.sqlite` is inaccessible, the agent falls back to direct turn execution with no workflow state recorded.
- **Recommended action:** Document fallback conditions explicitly in `agent/orchestrator.py`. Add test coverage for the fallback path.
- **Notes for AI reference:** WorkflowEngine is optional. Absence of `config/workflows/default.json` is the simplest way to disable it. Do not assume workflow state exists for turns executed before the workflow DB was available.

---

### OQ-03: Session title generation silently drops errors — no user feedback

- **Type:** Open Question / Needs confirmation
- **Impact scope:** `agent/commands/cmd_session.py _generate_session_title()`, `agent/services/session_title.py SessionTitleService`
- **Description:** `_generate_session_title()` is called via `asyncio.create_task()` (fire-and-forget) on the first turn of each session. On failure, the error is logged but no fallback title is generated and no user notification occurs. The session may remain with an empty or default title.
- **Current safe interpretation:** Session title generation failure is non-fatal. The session continues normally. Titles may be empty after LLM or config errors.
- **Recommended action:** Consider implementing a `first_input[:50]` fallback title on LLM failure (same as the older implementation described in source docs).
- **Notes for AI reference:** Do not rely on session titles being set after the first turn. Title generation is asynchronous and may fail silently.

---

## Undocumented Areas

### UNDOC-01: Memory layer (`agent/memory/`) has no standalone API reference in restructured docs

- **Type:** Undocumented
- **Impact scope:** `agent/memory/` package (layer, store, retriever, extract, jsonl_store, injection, ingestion, embedding_client)
- **Description:** The restructured `05_agent_*` files summarize the memory layer in `05_agent_02` and `05_agent_04`, but do not provide a standalone per-module API reference. The deleted `05_ref-agent-context.md` contained `AppServices.memory` field descriptions. Full memory API (e.g., `MemoryStore.get()`, `MemoryRetriever.retrieve()`, `extract_memories()`) is undocumented in the current restructured set.
- **Current safe interpretation:** Use `05_agent_04_state-and-persistence.md §Memory Services` and `05_agent_08_configuration.md §MemoryConfig` for available documentation.
- **Recommended action:** Add memory layer API reference to `05_agent_12_reference-api.md`, or create a dedicated `05_agent_04_memory_layer.md`.
- **Notes for AI reference:** For memory layer implementation details, read `agent/memory/` source files directly. `ctx.services.memory` is `None` when `use_memory_layer=False` (default).

---

### UNDOC-02: Plugin tool return value convention not enforced at registration time

- **Type:** Undocumented / Needs confirmation
- **Impact scope:** `shared/plugin_registry.py @register_tool`, `shared/tool_executor.py ToolExecutor.execute()`
- **Description:** `@register_tool` handlers must return `tuple[str, bool]` (`(result_text, is_error)`). This is documented in `05_agent_11_extension-points.md`, but there is no type enforcement or runtime validation at registration time. A handler returning the wrong type will fail silently or raise at call time.
- **Current safe interpretation:** Always return exactly `tuple[str, bool]` from `@register_tool` handlers. Mistyped returns will cause `ToolExecutor.execute()` to fail at call time, not at registration.
- **Recommended action:** Add a runtime type check or `Protocol`-based enforcement in `load_plugins()` or `ToolExecutor.execute()`.
- **Notes for AI reference:** Plugin tools bypass MCP routing and TTL cache. They are checked first in `ToolExecutor.execute()`. A plugin with the same name as an MCP tool shadows the MCP tool.
