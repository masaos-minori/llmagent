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

### OQ-01: AgentSession RAG-layer dependency

- **Type:** Resolved
- **Status:** Resolved as of boundary split
- `AgentSession` has zero RAG-layer imports. All RAG maintenance routes through `RagMaintenanceService`.
- Verified by `tests/test_mdq_rag_boundary.py::test_agent_layer_rag_sqlite_access_only_in_maintenance_service`.

---

### OQ-03: Session title generation — fallback behavior (RESOLVED)

- **Type:** Resolved
- **Status:** Resolved — fallback title IS implemented (see `cmd_session.py _generate_session_title()`)
- **Impact scope:** `agent/commands/cmd_session.py _generate_session_title()`, `agent/services/session_title.py SessionTitleService`
- **Description:** On `SessionTitleGenerationError`, a fallback title is derived from `first_input[:32]` (or `"(New Session)"` for empty input). The session always ends with a non-empty title. Failures are logged at WARNING + audit level.
- **Current safe interpretation:** Session title generation failure is non-fatal. The fallback title is always persisted. See `05_agent_04 §Session Title Generation Failure Behavior` for full failure table.
- **Notes for AI reference:** Session titles are set non-blocking. After the first turn, the title will be the LLM-generated title or the truncated first user input — never empty.

---

### Session SQLite corruption recovery gap

- **Type:** Known Gap
- `/db recover` (compatibility alias) and `/db rag recover` target `rag.sqlite` only (via `RagMaintenanceService`)
- `/db session recover [backup-path]` now exists: calls `DbMaintenanceService.recover_session()` → `recover_corruption(backup_path, target="session")`
- Operator path: `/db session recover /path/to/backup.sqlite`

---

## Undocumented Areas

### UNDOC-01: Memory layer (`agent/memory/`) — standalone doc added

- **Type:** Resolved
- **Status:** Resolved — `05_agent_12_memory.md` now documents the full memory layer.
- **Backend:** SQLite (`memories` table + `memories_fts` FTS5 + optional `memories_vec` vector index) + JSONL file. Backend: **Implemented**.
- **Commands:** `/memory list`, `/memory save`, `/memory search`, `/memory delete`, `/memory prune`
- **Search strategies:** FTS5 (keyword), KNN (vector similarity), Hybrid (RRF merge)
- **Notes for AI reference:** `ctx.services.memory` is `None` when `use_memory_layer=False` (default). Always null-check before calling any memory method.

---

### UNDOC-02: Plugin tool return value convention not enforced at registration time

- **Type:** Addressed (runtime enforcement exists at call time)
- **Impact scope:** `shared/plugin_registry.py @register_tool`, `shared/tool_executor.py ToolExecutor.execute()`
- **Current state:** `ToolExecutor.execute()` validates the return value at call time: checks `isinstance(result_raw, tuple)`, `len >= 2`, `isinstance(output, str)`, `isinstance(is_error, bool)` — raises `ValueError` or `TypeError` on mismatch. No enforcement at `@register_tool` decoration time.
- **Current safe interpretation:** Return type errors surface on the first call, not at startup. Convention `tuple[str, bool]` is documented in `05_agent_11_extension-points.md`.
- **Notes for AI reference:** Plugin tools bypass MCP routing and TTL cache. A plugin with the same name as an MCP tool shadows the MCP tool.

---
