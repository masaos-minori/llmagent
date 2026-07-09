# MCP Inconsistencies and Known Issues

This file catalogs bugs, unimplemented features, spec conflicts, and undefined behavior
in the MCP layer discovered during documentation restructuring.

Each entry format:
- **Type:** `Implementation bug` / `Unimplemented` / `Document inconsistency` / `Undefined` / `Needs confirmation`
- **Impact scope:** Affected modules/behavior
- **Statement A / B:** Conflicting facts (when applicable)
- **Current safe interpretation:** What to assume when uncertain
- **Recommended action:** Fix or investigation needed
- **Notes for AI reference:** Guidance for AI reasoning about this issue

---



## Active Issues

*(現在アクティブな問題はありません)*

---

## Resolved Issues

### BUG-01: MCP reload mutates running config instead of reporting restart-required

- **Type:** Resolved (fixed 2026-07-09 — was `Implementation bug`)
- **Impact scope:** `agent/services/config_reload.py`, `agent/config_dataclasses.py`,
  `agent/config_builders.py`, `agent/commands/cmd_config_display.py`, `shared/tool_executor.py`,
  `agent/repl_health.py`, `config/agent.toml`, plus 20 test files and 6 documentation files.
- **Statement A (was true until 2026-07-09):** `_apply_mcp_url_reload()` mutated
  `ctx.cfg.mcp.mcp_servers[key].url` at runtime for HTTP transport changes, and stored
  `auth_token`/`startup_mode` changes as `deferred`. The legacy `github_server_url` field
  was still read/written and displayed.
- **Fix applied:** `_apply_mcp_url_reload()` replaced with `_classify_mcp_server_changes()` /
  `_diff_mcp_server_config()` in `config_reload.py` — every `McpServerConfig` field change,
  server add/remove/rename is now reported as `mcp/<server>.<field>` (or
  `mcp/<server> (new server)` / `(removed server)`) in `ConfigReloadOutcome.needs_restart`,
  and `ctx.cfg.mcp.mcp_servers` is never mutated. `github_server_url` removed from
  `MCPConfig`, `build_agent_config()` (now rejected with `ConfigLoadError`), the reload
  handler, the `/config` display, and the shipped `config/agent.toml` sample. Implemented
  per the plans/implementation docs referenced from requirements H-1 through L-3
  (`requires/done/20260708_23_require.md` through `requires/done/20260708_41_require.md`).
- **Verification:** All directly affected test files pass (`test_config_reload.py`,
  `test_config_reload_classification.py`, `test_watchdog.py`, `test_cmd_config_refactor.py`,
  `test_agent_cmd_config.py`, `test_cmd_config_char.py`, `test_config_builders.py`,
  `test_tool_executor_routing.py`, `test_cmd_mcp.py`, and 11 fixture files that referenced
  `github_server_url`). `ruff`, `mypy`, and `lint-imports` pass on all changed files. A full
  repo-wide `pytest` run was not completed to conclusion in this session (interrupted
  twice by session/background-task boundaries); one pre-existing, unrelated failure
  (`test_robustness_chaos.py::TestNetworkChaos::test_3d1_intermittent_502s`) was confirmed
  via `git stash` to fail identically before this change, so it is not a regression.
- **Notes for AI reference:** MCP server definition changes are restart-required only —
  do not reintroduce hot-reload or deferred handling for any `McpServerConfig` field. The
  GitHub MCP endpoint is configured only through `mcp_servers.github.url`; `github_server_url`
  is a rejected config key.

---
