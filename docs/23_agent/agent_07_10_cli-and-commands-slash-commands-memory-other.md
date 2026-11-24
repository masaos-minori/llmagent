---
title: "Agent CLI and Commands - Slash Commands: Other and Retired Memory Commands"
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
  - agent_07_07_cli-and-commands-slash-commands-session-mcp.md
  - agent_07_08_cli-and-commands-slash-commands-context-plan.md
  - agent_07_09_cli-and-commands-slash-commands-workflow-debug.md
  - agent_01_system-overview.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the retired `/memory` command and the purpose of the slash commands in the Other category.

## Design Intent

### Retired Memory Commands

The `/memory` command and its subcommands (status, list, delete, pin, unpin, prune, reindex, rebuild) are retired by ADR-008. No compatibility alias is retained, and the command is not part of the supported CLI contract. It is still registered in code until it is removed (SHARED-003).

Episodic Memory has no user-facing add, list, search, pin, delete, prune, or rebuild operation: it is generated and managed internally. Its diagnostics belong to `/stats`, `/context`, `/debug verbose`, and `/reload`, and Repository Context reload belongs to `/reload` (see [agent_07_06](agent_07_06_cli-and-commands-hot-reload.md)).

The usage forms below are listed only because the command registry still registers them and the documentation checks require every registered usage to appear in a chapter. They are retired, have no documented effect, and are removed from this list when the code removal lands (SHARED-003).

| Retired usage form | Status |
|---|---|
| `/memory status` | Retired |
| `/memory list [n] [--type semantic\|episodic] [--pinned] [--query <text>]` | Retired (default 20, at most 200) |
| `/memory delete <memory_id>` | Retired |
| `/memory pin <memory_id>` | Retired |
| `/memory unpin <memory_id>` | Retired |
| `/memory prune [--days <n>]` | Retired |
| `/memory reindex [--fts\|--vec]` | Retired |
| `/memory rebuild [--confirm] [--allow-loss]` | Retired |

### Other Category

`/help` displays this help output.

## Responsibility Boundary

- **Memory**: None; the memory commands are retired
- **Other**: Help display

## Keywords

- retired memory commands
