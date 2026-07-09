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

*(No undocumented areas currently tracked. UNDOC-02 "Plugin tool return
value convention not enforced at registration time" was removed
2026-07-09 — `05_agent_11_extension-points.md` §`@register_tool` now
documents fail-fast return-annotation validation at registration time
(`ValueError` if missing/wrong, verified against
`shared/plugin_registry.py::register_tool()`), in addition to the runtime
value validation in `ToolExecutor.execute()`. Both layers are enforced and
documented; the gap this entry tracked no longer exists.)*

---


