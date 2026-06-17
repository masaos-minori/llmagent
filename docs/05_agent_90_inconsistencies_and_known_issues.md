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

- **Type:** RESOLVED (Document inconsistency)
- **Resolution:** All remaining stale references removed: `shared/tool_constants.py` comment updated (`agent/tool_policy.py` is now the correct reference); "Extracted from repl_tool_exec.py" lines removed from module docstrings in `tool_policy.py`, `tool_approval.py`, `tool_runner.py`, `tool_audit.py`, `tool_result_formatter.py`.
- **Notes for AI reference:** `ToolExecutor` in `shared/tool_executor.py` is the single authoritative tool execution entry point. Risk classification lives in `agent/tool_policy.py`. See `05_agent_06_tool-execution-and-approval.md`.

---

### DOC-02: `ServerLifecycleManager` was deleted from `agent/lifecycle.py`

- **Type:** RESOLVED (Document inconsistency)
- **Resolution:** Verified: no remaining imports of the old monolithic `ServerLifecycleManager`. Stale comment in `factory.py` updated (`ServerLifecycleManager` → `_ServerLifecycleRouter`). Stale reference to `05_ref-agent-context.md §6` removed from `05_agent_02_runtime-architecture.md`.
- **Notes for AI reference:** `_ServerLifecycleRouter` (private class in `factory.py`) is the canonical lifecycle coordinator; it delegates to `HttpServerLifecycleManager` (`http_lifecycle.py`) and `StdioServerLifecycleManager` (`stdio_lifecycle.py`).

---

### DOC-03: `MCPConfig.github_url` field name differs from `github_server_url` config key

- **Type:** RESOLVED (Document inconsistency / naming misalignment — fixed)
- **Resolution:** `MCPConfig.github_url` renamed to `MCPConfig.github_server_url`. All callers updated: `config_builders.py`, `config_reload.py`, `cmd_config_display.py`, `tests/test_agent_cmd_config.py`. Doc table in `05_agent_08_configuration.md` updated. TOML key and dataclass field are now identical.
- **Notes for AI reference:** Use `ctx.cfg.mcp.github_server_url`. In `config/agent.toml`, the key is `github_server_url`.

---

### DOC-04: `05_agent_00` Known Limitations references deleted file `05_ref-agent-context.md`

- **Type:** RESOLVED (Document inconsistency — stale reference removed)
- **Resolution:** `05_agent_00_document-guide.md §Known Limitations` no longer references `05_ref-agent-context.md`; text now reads "No standalone per-module API reference exists in the restructured set." Remaining reference in `05_agent_02_runtime-architecture.md §ServerLifecycleManager Deletion` also removed.
- **Notes for AI reference:** `05_ref-agent-context.md` does not exist. Memory layer API: see `05_agent_02 §Memory Services` and `05_agent_04_state-and-persistence.md`.

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

- **Type:** RESOLVED (Implementation bug — fixed)
- **Impact scope:** `shared/tool_executor.py ToolExecutor._raw_execute()`, `shared/mcp_config.py McpServerHealthRegistry`
- **Resolution:** `record_failure()` and `record_success()` are now called in `_raw_execute()`. The HEALTHY → DEGRADED → UNAVAILABLE state machine is active. See full details in [`04_mcp_90_inconsistencies_and_known_issues.md §BUG-01`](04_mcp_90_inconsistencies_and_known_issues.md).
- **Notes for AI reference:** Health state transitions are now functional. Servers accumulating transport failures transition to DEGRADED then UNAVAILABLE and are blocked from dispatch until a successful call resets them to HEALTHY.

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

- **Type:** RESOLVED
- **Impact scope:** `agent/workflow/`, `agent/orchestrator.py Orchestrator.handle_turn()`
- **Resolution:** Workflow mode is now explicit via `workflow_mode` field on `AgentConfig`. Three modes: `"auto"` (implicit fallback with warning log), `"required"` (raises `RuntimeError` on any unavailability), `"disabled"` (always direct execution, no loader attempted). Default is `"auto"` for backward compatibility. Fallback conditions are: (1) workflow definition file not loaded, (2) `StateStore()` raises `RuntimeError`. Both are logged at `WARNING` level in `auto` mode and raise in `required` mode. Test coverage added in `tests/test_orchestrator.py`.
- **Notes for AI reference:** WorkflowEngine is optional. Set `workflow_mode = "disabled"` in agent config to unconditionally skip it. `workflow_mode = "required"` enforces hard failure if either workflow JSON or `workflow.sqlite` is unavailable.

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
