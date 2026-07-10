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

l

- **Prompt:** `agent>` (no session) or `agent[:#N]>` (N = session_id)
- **Normal input:** any text → forwarded to `Orchestrator.handle_turn()`
- **Slash commands:** lines starting with `/` → `CommandRegistry.dispatch(line)`
- **Multiline input:** line ending with `\` → continues with `... ` prompt
- **EOF / Ctrl-D:** graceful shutdown
- **Ctrl-C:** interrupts current line; does not exit REPL

---

## CLIView (`agent/cli_vi

ew.py`)

Presentation layer only. Injected as callbacks into components.

### Callbacks

| Callback | Injected into | Called when |
|---|---|---|
| `write_token(token)` | `LLMClient(on_token=...)` | Each SSE token arrives |
| `write_compress_notice(n)` | `HistoryManager(on_compress=...)` | History compressed |
| `write_turn_start()` | `Orchestrator(on_turn_start=...)` | Before each tool-loop turn |
| `write_turn_end()` | `Orchestrator(on_turn_end=...)` | After final LLM answer |
| `write_llm_error(e)` | `Orchestrator(on_error=...)` | LLM request failure |

### Key methods

| Method | Output |
|---|---|
| `setup_readline()` | Tab completion (slash commands), emacs edit mode, history file load |
| `write_progress(msg)` | `  [rag] {msg:<24}` in-place overwrite (`\r`) |
| `clear_progress()` | Erase progress line with spaces |
| `write_warning(msg)` | `[warn] {msg}` |
| `write_startup_banner(chunk_count, n_tools)` | `DB: {n} chunks \| Tools: {n}` |
| `write_history()` | Save readline history to `~/.agent_history` (max 1000 entries) |
| `async read_multiline(loop, first_line)` | Collect `\`-terminated lines; join with `\n` |

### Protocols (for testing)

`Writer` protocol (output operations) and `Reader` protocol (multiline input).
Tests can inject alternative implementations instead of the real CLIView.

---

## CommandRegistry (`agen

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
