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

### Session SQLite corruption recovery gap

- `/db rag recover [backup-path]` targets `rag.sqlite` only (via `RagMaintenanceService`)
- `/db session recover [backup-path]` exists: calls `DbMaintenanceService.recover_session()` → `recover_corruption(backup_path, target="session")`
- Operator path: `/db session recover /path/to/backup.sqlite`

---

## Undocumented Areas

### UNDOC-02: Plugin tool return value convention not enforced at registration time

- **Type:** Addressed (runtime enforcement exists at call time)
- **Impact scope:** `shared/plugin_registry.py @register_tool`, `shared/tool_executor.py ToolExecutor.execute()`
- **Current state:** `ToolExecutor.execute()` validates the return value at call time: checks `isinstance(result_raw, tuple)`, `len >= 2`, `isinstance(output, str)`, `isinstance(is_error, bool)` — raises `ValueError` or `TypeError` on mismatch. No enforcement at `@register_tool` decoration time.
- **Current safe interpretation:** Return type errors surface on the first call, not at startup. Convention `tuple[str, bool]` is documented in `05_agent_11_extension-points.md`.
- **Notes for AI reference:** Plugin tools bypass MCP routing and TTL cache. A plugin with the same name as an MCP tool shadows the MCP tool.

---

## Document Inconsistencies

### DISC-03: branch field in memory retrieval

- **Type:** Undocumented behavior
- **Impact scope:** `05_agent_12_memory.md` (line 190 — branch described only as "for context filtering")
- **Statement A:** `branch` field is stored metadata for context filtering (implied by doc)
- **Statement B:** `branch` is actively used in `FtsRetriever._context_boost()` as a relevance rescoring signal; records without matching branch are still returned but ranked lower
- **Current safe interpretation:** Branch affects ranking, not filtering — it is an active retrieval parameter

### DISC-04: workflow_mode=required startup blocking scope

- **Type:** Needs confirmation
- **Impact scope:** `05_agent_08_configuration.md` (workflow_mode description)
- **Statement A:** `workflow_mode = "required"` raises `RuntimeError` when `WorkflowLoader` fails during `Orchestrator.__init__()`
- **Statement B:** Unclear whether failure is at agent startup or at first turn — depends on whether `StartupOrchestrator.run()` catches this
- **Current safe interpretation:** Failure occurs during agent boot (Orchestrator construction phase), not at the first turn

### DISC-05: memory SQLite DB location

- **Type:** Document inconsistency
- **Impact scope:** `05_agent_09_data-layer.md` (line 130 — "session.sqlite or separate")
- **Statement A:** Memory tables (`memories`, `memories_fts`, `memories_vec`) are in "session.sqlite or separate" (ambiguous)
- **Statement B:** All memory tables live in `session.sqlite` — verified by `SQLiteHelper("session")` usage throughout `scripts/agent/memory/store.py` and `retriever.py`
- **Current safe interpretation:** Memory tables are in `session.sqlite`, same DB as sessions/messages

---
