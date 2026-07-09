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

### DISC-04: workflow_mode config key no longer exists; docs still describe required/auto/disabled modes

- **Type:** Resolved (docs corrected 2026-07-09 — was "Needs confirmation", then "Document inconsistency")
- **Impact scope:** `05_agent_08_configuration.md`, `05_agent_10_operations-and-observability.md`
  (both describe `workflow_mode = "required"` / `"auto"` / `"disabled"`); actual code:
  `agent/config_builders.py::build_agent_config()`, `agent/orchestrator.py::Orchestrator.__init__()`
- **Statement A (docs):** `05_agent_08_configuration.md` and
  `05_agent_10_operations-and-observability.md` describe `workflow_mode` as a live,
  three-valued config setting (`"required"` raises `RuntimeError` on `WorkflowLoader`
  failure; `"auto"` falls back to direct LLM with a warning; `"disabled"` skips workflow
  tracking) and call it "a startup-only setting" changeable only via config file + restart.
- **Statement B (implementation, verified 2026-07-09):** `workflow_mode` is now one of the
  `_FORBIDDEN_KEYS` in `build_agent_config()` (`config_builders.py:261`) — any config
  containing this key raises `ConfigLoadError` at load time. `Orchestrator.__init__()`
  (`orchestrator.py:123-129`) no longer branches on any mode: it unconditionally calls
  `WorkflowLoader().load()` and raises `RuntimeError` on **any** failure (`except
  (WorkflowLoadError, Exception)`), with no `"auto"` degraded-fallback or `"disabled"`
  skip path. `grep -rn "workflow_mode" scripts/ --include=*.py` (excluding tests) shows no
  other reference besides the forbidden-key entry and one unused
  `agent/services/models.py:104` dataclass field.
- **Current safe interpretation:** `workflow_mode` is not a supported config key — setting
  it in any config file causes the agent to fail to start with `ConfigLoadError`. A missing
  or invalid workflow definition always raises `RuntimeError` during
  `Orchestrator.__init__()` (agent boot, not first turn) — there is no way to run in a
  degraded or workflow-disabled mode via configuration.
- **Recommended action:** ~~Update `05_agent_08_configuration.md` and
  `05_agent_10_operations-and-observability.md`~~ — **done 2026-07-09**: both now describe
  the actual unconditional-`RuntimeError`/preflight-check behavior and state that
  `workflow_mode` is a rejected config key, not a startup-only toggle. Remaining follow-ups,
  not yet done:
  - `services/models.py:104`'s `workflow_mode` field (on `ContextStateView`) is confirmed
    dead — its sole constructor call site (`context_view.py:158`) never passes it, so it is
    always the dataclass default `""`; safe to remove separately as an unrelated cleanup.
  - ~~`config/agent.toml:18` still sets `workflow_mode = "auto"`~~ — **fixed 2026-07-09**:
    line removed. This had been a live bug (agent failed to start with `ConfigLoadError`
    from the shipped default config), not just a doc issue — confirmed no other
    `_FORBIDDEN_KEYS` member (`workflow_require_approval`, `use_tool_summarize`,
    `tool_summarize_threshold`) remains anywhere under `config/`.
- **Notes for AI reference:** Do not tell a user to set `workflow_mode = "disabled"` or
  `"auto"` to work around a missing workflow definition — that key is rejected at config
  load. The only way to avoid the startup `RuntimeError` is to provide a valid workflow
  definition at `WORKFLOWS_DIR / "default.json"`.

### DISC-05: MCP reload/config docs describe soon-to-be-removed hot-reload and deferred behavior

- **Type:** Document inconsistency
- **Impact scope:** `05_agent_08_configuration.md`, `05_agent_07_cli-and-commands.md` (MCP reload classification wording)
- **Statement A:** These docs currently describe MCP HTTP URL as
  hot-reloadable and `auth_token`/`startup_mode` as deferred.
- **Statement B:** Requirements H-1 through L-2
  (`requires/done/20260708_23_require.md` through
  `requires/done/20260708_40_require.md`) have approved plans to make all
  MCP server definition changes restart-required and remove
  `github_server_url`; see
  [MCP known issues: BUG-01](04_mcp_90_inconsistencies_and_known_issues.md)
  for the implementation-side tracking entry.
- **Current safe interpretation:** Treat the docs as describing the
  pre-change behavior until the linked plans are implemented and these docs
  are updated per their Design sections.

---
