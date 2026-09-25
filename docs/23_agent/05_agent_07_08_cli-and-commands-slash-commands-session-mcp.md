---
title: "Agent CLI and Commands - Slash Commands: Session, MCP, Config/Stats"
area: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md
---

# Agent CLI and Commands

- System Overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Session, MCP, and Config/Stats categories.

## Design Intent

### Session Category

A group of commands for session management and history operations. `/clear new` starts a new DB session. `/undo` pops the most recent user+assistant turn from both the history and the DB.

#### Session DB operation subcommands

All legacy `/db session <subcmd>` subcommands have been migrated to `/session <subcmd>`. For details, see [Context/DB Category](05_agent_07_09_cli-and-commands-slash-commands-context-db.md).

### MCP Category

`/mcp` / `/mcp status` provides a health view of the **currently running** MCP server settings; it is not a preview of pending `/reload` changes.

The output of `/mcp status` includes a list of servers, a list of servers in DEGRADED/UNAVAILABLE states, and serialization event statistics.

### Config / Stats Category

A group of commands for displaying and monitoring configuration files. `/reload` reloads all configuration files and updates `ctx.cfg` to synchronize with services.

## Responsibility Boundary

- **Session**: Lifecycle management of sessions and history
- **MCP**: Health and tool list of MCP servers
- **Config/Stats**: Displaying configuration and metrics

## Key Constraints

- Unknown

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_07_01_cli-and-commands-cli-reference.md`
- `05_agent_07_02_cli-and-commands-cliview.md`
- `05_agent_07_03_cli-and-commands-command-registry.md`
- `05_agent_07_04_cli-and-commands-purpose.md`
- `05_agent_07_05_cli-and-commands-repl-io.md`
- `05_agent_07_06_cli-and-commands-hot-reload.md`
- `05_agent_07_07_cli-and-commands-migration-notes.md`
- `05_agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `04_mcp_06_12_watchdog-configuration-monitoring.md`
- `05_agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `05_agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

slash command reference
session category
mcp category
config/stats category
