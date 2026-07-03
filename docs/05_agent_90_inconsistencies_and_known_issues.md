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

### DISC-03: branch field in memory retrieval -- RESOLVED

- **Type:** Document inconsistency (resolved)
- **Impact scope:** `05_agent_12_memory.md`
- **Resolution:** Branch filtering is implemented as a hard SQL predicate
  `AND (? = '' OR m.branch = '' OR m.branch = ?)` in both `FtsRetriever` and
  `VectorRetriever`. Memories from non-matching branches are **excluded**, not merely
  ranked lower. Global memories (`branch = ''`) are always included. An additional scoring
  boost is applied by `scoring.context_boost()` when branch matches.
  `05_agent_12_memory.md` has been updated to reflect this behavior.
- **Notes for AI reference:** `FtsRetriever._context_boost()` does not exist. Scoring is
  in `scoring.context_boost()` in `scripts/agent/memory/scoring.py`.

### DISC-04: workflow_mode=required startup blocking scope

- **Type:** Needs confirmation
- **Impact scope:** `05_agent_08_configuration.md` (workflow_mode description)
- **Statement A:** `workflow_mode = "required"` raises `RuntimeError` when `WorkflowLoader` fails during `Orchestrator.__init__()`
- **Statement B:** Unclear whether failure is at agent startup or at first turn — depends on whether `StartupOrchestrator.run()` catches this
- **Current safe interpretation:** Failure occurs during agent boot (Orchestrator construction phase), not at the first turn

---
