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

The reload subcommand reads the base configuration files, builds a candidate through the same parser
startup uses, prepares every change the candidate names, and commits them through a staged transaction.
Settings that cannot take effect in the running process — startup-only fields and MCP server
definitions — are recorded as pending restart instead of being applied.

### Change Classification

| Category | Output Tag | Description |
|---|---|---|
| Hot-reloadable | `[OK]` | Applied immediately to the running process |
| Requires restart | `[RESTART]` | MCP server definition change. A full restart of the agent is required |
| Startup-only | `[STARTUP-ONLY]` | Loaded only once at startup. Recorded as pending restart, never applied by reload |
| Skipped | `[SKIP]` | Changes intentionally ignored |
| Always live | `[LIVE]` | Always effective without reload |

### Reload Stages

`/reload` prints the stage it ended in as its first line, `Reload stage: <stage>`:

- `prepared`: everything validated, nothing applied. Covers the no-change case, the pending-only case,
  and any failure while preparing.
- `committed`: every prepared step is live.
- `rolled_back`: a commit failure was undone in full, so the live configuration is what it was before
  the command.
- `degraded`: a rollback failure left live state inconsistent. A restart is required, and a later
  `/reload` is refused until the process restarts.

A candidate that fails validation never reaches the commit phase: no configuration section, no service
step, and no Repository Context snapshot changes, and the reported error names the field and the rule it
broke rather than the configured value. A key no section recognizes is rejected for the same reason.

Commit runs the prepared steps in a fixed order — configuration sections, conversation state, runtime
tool policy, history, LLM hot-config — and each step carries the undo token captured before it applied.

### Pending Restart Display

Startup-only fields and MCP server definitions stay pending until the process restarts:

- `/reload` and `/config` list pending startup-only fields under `Pending restart (not applied to
  the running process)`. The list is the container's pending state, so a field an earlier `/reload`
  recorded is still listed.
- `/mcp status` lists pending MCP definitions under their own heading and never shows a pending
  definition as a live server row.
- A pending record names the field path only; it never carries the configured value.

### Repository Context Reload

`/reload` also reloads Repository Context from the explicitly configured repository files:

- All sources are loaded into a candidate snapshot first.
- A validation failure rejects the complete reload and preserves the active snapshot.
- The new snapshot applies only to subsequent turns; a turn already running keeps the snapshot it started with.
- Repository Context is never persisted: it is not stored in SQLite or JSONL and not in the Session DB backup.

The Repository Context loader and this reload behavior are not implemented yet (SHARED-003). Its source list and configuration keys are undefined.

## Responsibility Boundary

- **Hot-reloadable**: the `CONFIG_FIELD_REGISTRY` entries marked hot-reloadable — LLM endpoint and
  generation settings, tool policy and allow lists, approval path lists, memory retrieval settings.
- **Requires restart**: MCP server definitions, and `tokenize_url`, which the registry does not carry.
- **Startup-only**: the registry entries read only at process startup — the three context limits,
  `use_memory_layer`, `memory_embed_enabled`, `approval_medium_preview_fallback`, `gitops_push_blocked`.

## Operational Notes

- For full classification of each field, see [Configuration: Hot-Reloadable Scope](agent_08_01_configuration-loading-agent-config.md#hot-reloadable-scope).

## Keywords

- hot-reload scope
- reload subcommand
- change classification
- reload stage
- pending restart
