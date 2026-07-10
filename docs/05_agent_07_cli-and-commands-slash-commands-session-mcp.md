---
title: "Agent CLI and Commands"
category: agent
tags:
  - agent
  - agent
  - cli
  - commands
  - repl
  - slash-commands
related:
  - 05_agent_00_document-guide.md
---

# Agent CLI and Commands

e

### Session category

| Command | Side effects | Related state |
|---|---|---|
| `/session list [n]` | None | Read `sessions` table |
| `/session load <id>` | Replaces `ctx.conv.history` | `ctx.session.session_id` updated |
| `/session rename <title>` | UPDATE `sessions.title` | None |
| `/session delete <id>` | DELETE session + messages (CASCADE) | Cannot delete current session |
| `/clear [new]` | Resets history; clears stats + cache | `new` → new DB session started |
| `/undo` | Pops last user+assistant turn from history + DB | Also removes memory injections |
| `/history [n]` | None | Display last N user/assistant messages |
| `/export [md\|json] [file]` | File write (if filename given) | None |

### MCP category

| Command | Side effects | Related state |
|---|---|---|
| `/mcp` | HTTP probe to all MCP servers | Displays health table (running config only) |
| `/mcp status` | HTTP probe to all MCP servers | Displays health table (running config only) |

`/mcp` / `/mcp status` is a health view of the **currently running** MCP
server configuration — it is not a preview of pending `/reload` changes.
After `/reload` reports `[RESTART]` items, `/mcp` continues to show the
pre-reload servers, URLs, and auth state until the agent is actually
restarted.

### Config / stats category

| Command | Side effects | Related state |
|---|---|---|
| `/config` | None | Display config file paths + values |
| `/stats` | None | Display session metrics |
| `/set temperature <f>` | Updates `ctx.cfg.llm.llm_temperature` + the LLM service's internal temperature field | Immediate LLM effect |
| `/set max_tokens <n>` | Updates `ctx.cfg.llm.llm_max_tokens` | Immediate LLM effect |
| `/reload` | Reloads all config files | Updates `ctx.cfg` and syncs services |

## Related Documents

- `agent`
- `cli`
- `commands`

## Keywords

agent
cli
commands
repl
slash-commands
