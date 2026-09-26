---
title: "Agent CLI and Commands - Slash Commands: Memory, MDQ, Other"
area: agent
tags:
  - agent
  - cli
  - slash-commands
related:
  - agent_00_document-guide.md
source:
  - agent_07_11_cli-and-commands-slash-commands-memory-other.md
---

# Agent CLI and Commands

- System Overview → [agent_01_system-overview.md](agent_01_system-overview.md)

## Purpose

Documents the purpose and side effects of slash commands in the Memory, MDQ, and Skill categories.

## Design Intent

### Memory Category

A group of commands for long-term memory. `/memory rebuild` performs DELETE + INSERT for all memories from JSONL (JSONL is the source of truth).

### MDQ Category

All `/mdq` commands call MCP tools of `mdq-mcp` via the agent's tool executor. MDQ uses `mdq.sqlite` (separate from `rag.sqlite`). For the distinction between MDQ and RAG, see [MDQ vs RAG Boundary](../22_mcp/mcp_05_04_mdq-rag-boundary.md#mdq-vs-rag-boundary).

### Skill Category

`/skill` displays a list of directory names under `skills/` (no LLM call occurs).

`/skill <name> [args]` passes the content of `skills/<name>/SKILL.md` to the next LLM turn. Re-running within the same session replaces the previous one.

**Known Limitation:** The message constructed by `_cmd_skill()` has both `_ephemeral: True` and `_skill_ephemeral: True`, but since `TRUSTED_SOURCES["skill_mixin"]` only authorizes `_skill_ephemeral`, the `append_message()` validation fails, causing the `_ephemeral` key to be sanitized (removed, with a `warning` log) before saving. As a result, only `_skill_ephemeral: True` remains in history. This is a known and accepted behavior change; the impact is that the orchestrator's generic `_ephemeral`-based pre-turn clearing no longer automatically removes injected skill messages at the start of the next turn.

### Other Category

`/help` displays this help output.

## Responsibility Boundary

- **Memory**: Management of long-term memory entries
- **MDQ**: Document indexing and search
- **Skill**: Skill injection
- **Other**: Help display

## Key Constraints

- Unknown

## Operational Notes

- Unknown

## Known Limitations

- `/skill` ephemeral messages leave only `_skill_ephemeral: True` in history

## Related Docs

- `agent_00_document-guide.md`
- `agent_07_01_cli-and-commands-cli-reference.md`
- `agent_07_02_cli-and-commands-cliview.md`
- `agent_07_03_cli-and-commands-command-registry.md`
- `agent_07_04_cli-and-commands-purpose.md`
- `agent_07_05_cli-and-commands-repl-io.md`
- `agent_07_06_cli-and-commands-hot-reload.md`
- `agent_07_07_cli-and-commands-migration-notes.md`
- `agent_07_08_cli-and-commands-slash-commands-session-mcp.md`
- `agent_07_09_cli-and-commands-slash-commands-context-db.md`
- `agent_07_10_cli-and-commands-slash-commands-workflow-debug.md`
- `agent_07_11_cli-and-commands-slash-commands-memory-other.md`

## Keywords

memory category
mdq category
skill category
