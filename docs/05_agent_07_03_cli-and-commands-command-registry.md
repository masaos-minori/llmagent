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

t/commands/registry.py`)

All slash commands dispatched by `CommandRegistry.dispatch(line)`.

Lookup order:
1. Exact match or prefix match in the built-in command list
2. Plugin commands registered via `@register_command` decorator (lower priority)

Boundary: `line == name` (exact) or `line.startswith(name + " ")` (prefix).

### Module Ownership

| Module | Owns | Does NOT Own |
|--------|------|--------------|
| `command_defs.py` | `CommandDef`, `SubcommandSpec` dataclasses | Command list |
| `command_defs_list.py` | Built-in command definitions | Dispatch logic |
| `registry.py` | Dispatch behavior; imports command list from `command_defs_list` | Command list definition |

> **Future command additions:** add a new `CommandDef(...)` entry to `command_defs_list.py` only.
> Implement the corresponding handler in the appropriate mixin file.

---

## Slash Command Referenc

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
