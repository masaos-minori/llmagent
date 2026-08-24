---
title: "Agent CLI and Commands - Hot-Reload Scope"
area: agent
tags:
  - agent
  - cli
  - hot-reload
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_06_cli-and-commands-hot-reload.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Documents the scope of the `/reload` command and the classification of configuration changes.

## Design Intent

### Role of `/reload`

`/reload` reads the base configuration files and applies changes as much as possible. Settings that are only loaded at startup are detected but not applied.

### Configuration Files

`_BASE_CONFIG_FILES` in `config_loader.py` contains only one item: `("agent.toml",)`. Agent process settings are centralized in `config/agent.toml`. Descriptions assuming the legacy multi-file structure have been removed.

### Change Classification

| Category | Output Tag | Description |
|---|---|---|
| Hot-reloadable | `[OK]` | Applied immediately to the running process |
| Requires restart | `[RESTART]` | A full restart of the agent is required |
| Startup-only | `[STARTUP-ONLY]` | Loaded only once at startup. Ignored by `/reload` even if changed |
| Skipped | `[SKIP]` | Changes intentionally ignored |

### Output Messages

- No changes: `No changes detected.`
- All applied: `Config reloaded — all changes applied`
- I/O error: `Reload failed (I/O error): <message>`

## Responsibility Boundary

- **Hot-reloadable**: LLM settings, history management, tool settings, etc.
- **Requires restart**: MCP server settings, etc.
- **Startup-only**: Settings loaded only during process startup.

## Key Constraints

- Unknown

## Operational Notes

- For full classification of each field, see [Configuration: Config file reload eligibility](05_agent_08_01_configuration-loading-agent-config.md#config-file-ownership-and-hot-reload-eligibility).

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

hot-reload scope
/reload
change classification
