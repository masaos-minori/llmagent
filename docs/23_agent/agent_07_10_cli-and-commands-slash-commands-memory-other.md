---
title: "Agent CLI and Commands - Slash Commands: Memory and Other"
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

Documents the purpose and side effects of slash commands in the Memory and Other categories.

## Design Intent

### Memory Category

A group of commands for long-term memory. `/memory` without a subcommand runs `status`. When the memory layer is disabled, only `status` runs. Memory is created only by automatic extraction at session end; there is no command that writes or edits a memory.

| Subcommand | Form | Effect |
|---|---|---|
| `status` | `/memory status` | Shows mode, counts, and pinned count against `memory_max_pinned`; changes nothing |
| `list` | `/memory list [n] [--type semantic\|episodic] [--pinned] [--query <text>]` | Lists memories with short IDs (default 20, at most 200); the positional `n` accepts the shared `int()` grammar — `'+5'` and `'1_0'` are accepted, the 1..200 bound still applies, and non-ASCII decimal digits such as `'٣'` remain accepted because `int()` accepts them; changes nothing |
| `delete` | `/memory delete <memory_id>` | Deletes one memory from all four memory tables after a `y/N` confirmation |
| `pin` | `/memory pin <memory_id>` | Fixes a memory; no confirmation; refused at the pin limit |
| `unpin` | `/memory unpin <memory_id>` | Releases a memory; no confirmation |
| `prune` | `/memory prune [--days <n>]` | Deletes memories not updated for `n` days (default `memory_retention_days`), never pinned ones, after confirmation; all-or-nothing |
| `reindex` | `/memory reindex [--fts\|--vec]` | Rebuilds the indexes only; `memories` and the JSONL archive are unchanged |
| `rebuild` | `/memory rebuild [--confirm] [--allow-loss]` | Rebuilds memory from the JSONL archive |

An ID is a full `memory_id` or a short ID of at least 8 characters; an ambiguous or unknown ID changes nothing. Each state change updates SQLite first and then appends a change event to the JSONL archive; if the append fails, the SQLite change is kept and a warning says that `rebuild` will not reproduce it. Operations that change data are written to the audit log.

`rebuild` replays the JSONL archive from the start (memory lines, then `delete`, `pin`, and `unpin` events) to compute the final state. It is a dry run unless `--confirm` is passed; the dry run reports the entries to import, pins after the rebuild, entries that exist only in SQLite, entries that differ, and entries needing a new embedding. If any memory exists only in SQLite, `--confirm` alone refuses; `--allow-loss` takes effect only together with `--confirm`. Before applying, all current `memories` rows are written to a backup file, and the rebuild does not run if the backup fails. Use `reindex` for index inconsistencies and `rebuild` to recover the memories themselves. A delete or pin change that has no change event in the archive is not reproduced.

Only `/memory` commands delete, pin, unpin, prune, reindex, or rebuild long-term memory, and they never restore, delete, or compact conversation history. Session retention (`/session purge`) and memory retention (`/memory prune`) are independent. Memory backup and recovery use the JSONL archive and `/memory rebuild`, not `/session export`.

### Other Category

`/help` displays this help output.

## Responsibility Boundary

- **Memory**: Management of long-term memory entries
- **Other**: Help display

## Keywords

- memory category
