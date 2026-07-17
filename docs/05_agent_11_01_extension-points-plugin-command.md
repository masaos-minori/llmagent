---
title: "Agent Extension Points — Removed (2026-07-18)"
category: agent
tags:
  - agent
  - extension-points
  - removed-feature
related:
  - 05_agent_00_document-guide.md
  - 04_mcp_06_15_new-mcp-server-addition-checklist.md
source:
  - 05_agent_11_01_extension-points-plugin-command.md
---

# Agent Extension Points — Removed (2026-07-18)

The entire plugin subsystem (the `plugins/*.py` architecture, the `@register_command` /
`@register_tool` / `@register_pipeline_stage` decorators, `shared/plugin_registry.py` and its
supporting modules, `/plugin status`, and all associated configuration keys) was removed on
2026-07-18. See `requires/done/20260717_01_require.md` and `plans/done/20260717-123416_plan.md`
for the removal requirement and plan.

This chapter was formerly split across four files. Three have been deleted outright as part of
this removal (削除済み), since they had no inbound references once this note replaced the fourth:
`05_agent_11_02_extension-points-tool-registration-part1.md` (削除済み),
`05_agent_11_02_extension-points-tool-registration-part2.md` (削除済み), and
`05_agent_11_03_extension-points-registry-rules.md` (削除済み). This file (the fourth) is kept as a
removal note because it is still linked from `05_agent_00_document-guide.md` and
`05_agent_01_system-overview.md`.

Removed with it:

- `plugins/*.py` auto-discovery and loading (`shared/plugin_auto_discover.py`)
- `@register_command`, `@register_tool`, `@register_pipeline_stage` decorators and their registries
  (`shared/plugin_registry.py`, `shared/plugin_registries.py`)
- Tool/command name conflict detection against MCP tools and built-in commands
  (`shared/plugin_conflicts.py`)
- `PluginFailure` / `PluginLoadResult` / `PluginLoadError` (`shared/plugin_result.py`)
- `PluginToolInvoker` (`shared/plugin_tool_invoker.py`) and its call site in
  `ToolExecutor.execute()`
- The `plugin_strict` / `plugin_tool_override` config keys (`ToolConfig`, `config/agent.toml`),
  their `/reload` handling, and their `/config` display lines
- `/plugin status` (`scripts/agent/commands/cmd_plugins.py`, `_PluginsMixin`)
- The `plugin_strict` entry in `ProductionConfigValidator._REQUIRED_STRICT_KEYS`

**Not affected** — these remain in place, unchanged by the plugin removal:

- MCP tool routing and dispatch (`ToolExecutor`, `ToolRegistry`, `ToolRouteResolver`) — see
  [90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md](90_shared_03_02_runtime_and_execution-plugin-and-tool-runtime.md)
- `tool_safety_tiers` / `ProductionConfigValidator` — still validates every registered (MCP) tool;
  see [90_shared_03_01_runtime_and_execution-config-and-logging.md](90_shared_03_01_runtime_and_execution-config-and-logging.md) §2b
- The step-by-step procedure for adding a new MCP server — this chapter's old
  "新しい MCP サーバーの追加" section was a duplicate summary; the canonical checklist is
  [04_mcp_06_15_new-mcp-server-addition-checklist.md](04_mcp_06_15_new-mcp-server-addition-checklist.md)

All tools are now provided exclusively by MCP servers.

## Related Documents

- [05_agent_00_document-guide.md](05_agent_00_document-guide.md)
- [04_mcp_06_15_new-mcp-server-addition-checklist.md](04_mcp_06_15_new-mcp-server-addition-checklist.md)

## Keywords

plugin
removed
extension points
register_command
register_tool
register_pipeline_stage
