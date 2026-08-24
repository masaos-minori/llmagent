---
title: "Agent System Overview"
area: agent
tags:
  - agent
  - system
  - overview
related:
  - 05_agent_00_document-guide.md
  - 05_agent_02_runtime-architecture.md
  - 05_agent_03_01_turn-processing-flow-overview.md
  - 05_agent_07_01_cli-and-commands-cli-reference.md
---

# Agent System Overview

## Purpose

Provides a CLI REPL interface that communicates with MCP tool servers via LLM function calling, maintains multi-turn conversation history, and returns answers to the terminal.

## Design Intent

The system overview should answer "what does this agent do" and "how does it fit into the broader system," not "which class maps to which file." Component-level detail belongs in owning chapters; this chapter provides only the high-level map.

## Responsibility Boundary

**In scope:**
- CLI REPL (`python -m agent`, entry point: `scripts/agent/__main__.py`)
- Communication with MCP tool servers (HTTP)
- Multi-turn conversation via SQLite session persistence
- Slash command interface
- SSE streaming for LLM responses

**Out of scope:**
- RAG pipeline internals (`scripts/mcp_servers/rag_pipeline/` handles this via MCP)
- MCP server implementations
- Embedding servers

### High-Level Component Responsibilities

| Component | Responsibility |
|---|---|
| `AgentREPL` | Manages startup flow and REPL loop |
| `Orchestrator` | Memory injection → compression → LLM → tool loop |
| `AgentContext` | Session-scoped DI hub |
| `LLMClient` | SSE streaming, retry |
| `ToolExecutor` | MCP routing, TTL cache |
| `HistoryManager` | Character counting, LLM-based compression |
| `CommandRegistry` | All `/cmd` dispatch |
| `CLIView` | readline, progress display, multiline input |
| `AgentSession` | sessions/messages SQLite |
| `AgentConfig` | 7 sub-configs, hot-reload |
| `MemoryServices` | Optional semantic memory layer |

## Key Constraints

| Constraint | Value |
|---|---|
| Max tool turns per message | `max_tool_turns` (default 5) |
| History compression threshold | `context_char_limit` (default 8000 chars) |
| HTTP timeout | `http_timeout` (default 30.0 sec) |
| LLM retry limit | `llm_max_retries` (default 3) |
| Tool result cache TTL | `tool_cache_ttl` (default 300 sec) |

## Operational Notes

### Overall Tool-Calling Model

``` text
[1] User enters question at REPL prompt
[2] User message + tool definitions → LLM (SSE streaming)
[3] LLM returns tool_calls → execute via MCP servers
[4] Tool results added as "tool" role messages → re-send to LLM
[5] Steps [3]–[4] repeat up to max_tool_turns (default 5)
[6] Final answer displayed; conversation history carried to next turn
```

MCP servers are called via HTTP POST `/v1/call_tool`.

### Workflow Engine Execution

`agent/orchestrator.py`'s `Orchestrator.handle_turn()` uses a `WorkflowDef` loaded at startup via `WorkflowLoader().load()` (equivalent to `config/workflows/default.json`) to execute each user turn as three stages (plan/execute/verify) via `WorkflowEngine.run(task, plan_fn, execute_fn, verify_fn)`. The simple pattern diagram above corresponds to the LLM turn processing within `execute_fn` (memory injection → user message addition → history compression → LLM turn). If workflow definition loading fails, `Orchestrator.__init__()` raises `RuntimeError` and startup stops. During approval pending (`ctx.workflow.approval_pending`), new turns are rejected with an error prompting `/approve` or `/reject`. See `05_agent_03` (turn processing flow) for details.

### Session, SSE, and History Compression

**Sessions:** A SQLite session row is created each time REPL is executed. Messages are persisted per turn. Past conversations can be restored via `/session load <id>`.

**SSE Streaming:** LLM responses are streamed token-by-token via Server-Sent Events. `LLMClient` handles reconnection (up to `sse_reconnect_max`), heartbeat timeouts, and partial completion processing.

**History Compression:** When `ctx.conv.history` exceeds `context_char_limit` (default 8000 chars), `HistoryManager.compress()` summarizes the oldest turns via LLM. The most recent `history_protect_turns` (default 2) turns are always protected.

### Slash Commands

For the canonical command list, see [05_agent_07 Slash Command Reference](05_agent_07_01_cli-and-commands-cli-reference.md). The source of truth is `scripts/agent/commands/command_defs_list.py`'s `_COMMANDS`. When adding commands, update both this summary and the full reference table in the canonical command chapter.

## Known Limitations

N/A — no known limitations documented beyond those tracked in `05_agent_90_inconsistencies_and_known_issues.md`.

## Related Docs

- [05_agent_00_document-guide.md](05_agent_00_document-guide.md)
- [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
- [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
- [05_agent_04_01_state-and-persistence-state-model.md](05_agent_04_01_state-and-persistence-state-model.md)
- [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md)
- [05_agent_06_01_tool-execution-and-approval-execution.md](05_agent_06_01_tool-execution-and-approval-execution.md)
- [05_agent_07_01_cli-and-commands-cli-reference.md](05_agent_07_01_cli-and-commands-cli-reference.md)
- [05_agent_08_01_configuration-loading-agent-config.md](05_agent_08_01_configuration-loading-agent-config.md)
- [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)
- [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- [05_agent_13_reference-api.md](05_agent_13_reference-api.md)
