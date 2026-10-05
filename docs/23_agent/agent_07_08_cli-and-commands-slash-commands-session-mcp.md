---
title: "Agent CLI and Commands - Slash Commands: Session, MCP, Config/Stats"
area: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - agent_00_document-guide.md
  - agent_07_01_cli-and-commands-cli-reference.md
  - agent_07_02_cli-and-commands-cliview.md
  - agent_07_03_cli-and-commands-command-registry.md
  - agent_07_04_cli-and-commands-purpose.md
  - agent_07_05_cli-and-commands-repl-io.md
  - agent_07_06_cli-and-commands-hot-reload.md
  - agent_07_09_cli-and-commands-slash-commands-context-db.md
  - agent_07_10_cli-and-commands-slash-commands-workflow-debug.md
  - agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Session, MCP, and Config/Stats categories.

## Design Intent

### Session Category

A group of commands for session management and history operations. `/clear new` starts a new DB session. `/undo` pops the most recent user+assistant turn from both the history and the DB.

#### Session DB operation subcommands

Session subcommands are invoked as `/session <subcmd>`. This includes the maintenance subcommands (`stats`, `health`, `checkpoint`, `vacuum`, `purge`, `recover`, `rag-consistency`, `rag-rebuild-fts`, `rag-rebuild-vec`); see agent_04_03 for the services they call.

### MCP Category

`/mcp` / `/mcp status` provides a health view of the **currently running** MCP server settings; it is not a preview of pending `/reload` changes.

The output of `/mcp status` includes a list of servers, a list of servers in DEGRADED/UNAVAILABLE states, and serialization event statistics.

### Config / Stats Category

A group of commands for displaying and monitoring configuration files. `/reload` reloads all configuration files and updates `ctx.cfg` to synchronize with services.

## Responsibility Boundary

- **Session**: Lifecycle management of sessions and history
- **MCP**: Health and tool list of MCP servers
- **Config/Stats**: Displaying configuration and metrics

## Keywords

slash command reference
session category
mcp category
config/stats category
