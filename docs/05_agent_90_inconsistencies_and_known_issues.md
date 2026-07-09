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

## Document Inconsistencies

### DISC-05: MCP reload/config deferred references removed (2026-07-09)

- **Type:** Resolved (docs corrected 2026-07-09 — was `Document inconsistency`)
- **Impact scope:** `05_agent_08_configuration.md`, `05_agent_07_cli-and-commands.md`,
  `cmd_config.py`, `config_reload.py`
- **Statement A:** `05_agent_08_configuration.md` described MCP HTTP URL as
  hot-reloadable and described a `deferred` classification for `auth_token`/`startup_mode`.
  `cmd_config.py` rendered `[DEFER]` labels. `config_reload.py` had a `deferred: list[str]`
  field on `ConfigReloadOutcome`.
- **Fix applied 2026-07-09:** All `[DEFER]` rendering branches removed from `_cmd_reload()`
  in `cmd_config.py`. `deferred` field removed from `ConfigReloadOutcome` dataclass in
  `config_reload.py`. Corresponding test assertions and `TestCmdReloadDeferred` deleted.
  "Deferred" bullet/subsection/table-row removed from `05_agent_08_configuration.md`.
- **Remaining:** `05_agent_07_cli-and-commands.md` wording was already consistent
  (restart-required classification, no deferred mention). See
  [MCP known issues](04_mcp_90_inconsistencies_and_known_issues.md) for the broader
  restart-required migration.
- **Notes for AI reference:** MCP server definition changes are restart-required only;
  do not reintroduce hot-reload or deferred handling. Check `ConfigReloadOutcome.needs_restart`
  for affected field paths.

---
