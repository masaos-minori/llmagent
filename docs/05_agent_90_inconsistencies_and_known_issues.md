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

## Open Questions

### OQ-01: `AgentSession` owns RAG-layer table access — responsibility boundary unclear

- **Type:** Open Question / Needs confirmation
- **Impact scope:** `agent/session.py AgentSession`, `/db clean`, `/db stats` commands, `RAG` layer
- **Description:** `AgentSession` (`agent/session.py`) implements `delete_document(url)` and `list_documents()`, which directly access the RAG layer tables (`documents`, `chunks`, `chunks_vec`) in `rag.sqlite`. This makes the agent layer depend on the RAG schema.
- **Current safe interpretation:** The current implementation works. `AgentSession` accesses RAG tables for `/db clean` and `/db stats` as a convenience. This is a known responsibility boundary violation.
- **Recommended action:** Consider moving RAG document management to `rag-pipeline-mcp` and having agent commands call it via MCP. Track before any RAG layer schema refactoring.
- **Notes for AI reference:** When modifying `AgentSession`, be aware it contains both session-layer and RAG-layer operations. Do not assume `agent/session.py` touches only `session.sqlite`.

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

- **Type:** Addressed (partial)
- **Impact scope:** `agent/memory/` package (store, retriever, extract, jsonl_store, injection, ingestion, embedding_client)
- **Current state:** `05_agent_12_reference-api.md §MemoryServices` documents the top-level API: `on_session_start()`, `on_user_prompt(query, session_id)`, `on_session_stop()`, activation condition, and failure behavior. Per-module API for `MemoryStore`, `MemoryRetriever`, and `extract_memories()` is not in the restructured docs.
- **Remaining gap:** Detailed internals of `agent/memory/` sub-modules. Read source files directly for those.
- **Notes for AI reference:** `ctx.services.memory` is `None` when `use_memory_layer=False` (default). Always null-check before calling any memory method.

---

### UNDOC-02: Plugin tool return value convention not enforced at registration time

- **Type:** Addressed (runtime enforcement exists at call time)
- **Impact scope:** `shared/plugin_registry.py @register_tool`, `shared/tool_executor.py ToolExecutor.execute()`
- **Current state:** `ToolExecutor.execute()` validates the return value at call time: checks `isinstance(result_raw, tuple)`, `len >= 2`, `isinstance(output, str)`, `isinstance(is_error, bool)` — raises `ValueError` or `TypeError` on mismatch. No enforcement at `@register_tool` decoration time.
- **Current safe interpretation:** Return type errors surface on the first call, not at startup. Convention `tuple[str, bool]` is documented in `05_agent_11_extension-points.md`.
- **Notes for AI reference:** Plugin tools bypass MCP routing and TTL cache. A plugin with the same name as an MCP tool shadows the MCP tool.

---
