---
title: "Agent CLI and Commands - Hot-Reload Scope"
area: agent
tags:
  - agent
  - cli
  - hot-reload
related:
  - agent_00_document-guide.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_07_02_cli-and-commands-cliview.md
  - agent_07_03_cli-and-commands-command-registry.md
  - agent_07_04_cli-and-commands-purpose.md
  - agent_07_05_cli-and-commands-repl-io.md
  - agent_07_07_cli-and-commands-slash-commands-session-mcp.md
  - agent_07_08_cli-and-commands-slash-commands-context-plan.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_07_10_cli-and-commands-slash-commands-memory-other.md
  - agent_01_system-overview.md
  - agent_08_01_configuration-loading-agent-config.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the scope of the reload subcommand and the classification of configuration changes.

## Design Intent

### Role of reload subcommand

The reload subcommand reads the base configuration files and applies changes as much as possible. Settings that are only loaded at startup are detected but not applied.

### Change Classification

| Category | Output Tag | Description |
|---|---|---|
| Hot-reloadable | `[OK]` | Applied immediately to the running process |
| Requires restart | `[RESTART]` | A full restart of the agent is required |
| Startup-only | `[STARTUP-ONLY]` | Loaded only once at startup. Ignored by reload subcommand even if changed |
| Skipped | `[SKIP]` | Changes intentionally ignored |
| Always live | `[LIVE]` | Always effective without reload |

### Apply Atomicity

The reloadable set of settings is applied atomically. A successful reload applies
every reloadable change together; there is no partial application.

- On a single invalid reloadable field, the entire reload is rejected: the live
  configuration is left unchanged, no service is re-synced, and the failure is
  reported as an actionable error that names the offending field.
- This differs from startup-only settings, which are detected but never applied by
  the reload subcommand regardless of validity.
- Restart remains required for the "Requires restart" category; atomicity governs
  only the reloadable fields applied within a single reload.

### Repository Context Reload

`/reload` also reloads Repository Context from the explicitly configured repository files. Reload is atomic:

- All sources are loaded into a candidate snapshot first.
- A validation failure rejects the complete reload and preserves the active snapshot.
- The new snapshot applies only to subsequent turns; a turn already running keeps the snapshot it started with.
- Repository Context is never persisted: it is not stored in SQLite or JSONL and not in the Session DB backup.

The Repository Context loader and this reload behavior are not implemented yet (SHARED-003). Its source list and configuration keys are undefined.

## Responsibility Boundary

- **Hot-reloadable**: LLM settings, history management, tool settings, etc.
- **Requires restart**: MCP server settings, etc.
- **Startup-only**: Settings loaded only during process startup.

## Operational Notes

- For full classification of each field, see [Configuration: Hot-Reloadable Scope](agent_08_01_configuration-loading-agent-config.md#hot-reloadable-scope).

## Keywords

- hot-reload scope
- reload subcommand
- change classification
