# Agent System Overview

- Document guide → [05_agent_00_document-guide.md](05_agent_00_document-guide.md)

## Purpose

Provide a CLI REPL interface that uses LLM function calling to interact with MCP tool
servers, maintain multi-turn conversation history, and deliver answers to the terminal.

---

## Scope

**In scope:**
- CLI REPL (`python -m agent`, entry: `scripts/agent/__main__.py`)
- MCP tool server communication (HTTP and stdio)
- Multi-turn conversation via SQLite session persistence
- Slash command interface
- SSE streaming LLM responses

**Out of scope:**
- RAG pipeline internals (`scripts/mcp/rag_pipeline/` handles this via MCP)
- MCP server implementations
- Embedding server

---

## Entry Point and Interaction Model

```
python -m agent   (scripts/agent/__main__.py)
  → asyncio.run(AgentREPL().run())
  → REPL loop: agent[:#N]> prompt
  → User text → LLM (SSE streaming) → tool_calls → MCP → answer
```

- Prompt: `agent>` or `agent[:#N]>` (N = session ID)
- Line editing: readline (bash-compatible keybindings)
- History file: `~/.agent_history`
- Multiline input: trailing `\` continues to next line; `...` prompt

---

## Overall Tool-Calling Model

```
[1] User enters question at REPL prompt
[2] User message + tool definitions → LLM (SSE streaming)
[3] LLM returns tool_calls → execute via MCP servers
[4] Tool results added as "tool" role messages → re-send to LLM
[5] Steps [3]–[4] repeat up to max_tool_turns (default 5)
[6] Final answer displayed; conversation history carried to next turn
```

MCP servers are called via HTTP POST `/v1/call_tool` or stdio JSON-RPC.

---

## High-Level Component Map

| Component | Class | File | Role |
|---|---|---|---|
| REPL coordinator | `AgentREPL` | `agent/repl.py` | Owns startup flow and REPL loop |
| Turn orchestration | `Orchestrator` | `agent/orchestrator.py` | Memory injection → compress → LLM → tool loop |
| Shared state | `AgentContext` | `agent/context.py` | Per-session DI hub |
| LLM communication | `LLMClient` | `shared/llm_client.py` | SSE streaming, retry |
| Tool routing | `ToolExecutor` | `shared/tool_executor.py` | MCP routing, TTL cache |
| History management | `HistoryManager` | `agent/history.py` | Char counting, LLM compression |
| Slash commands | `CommandRegistry` | `agent/commands/registry.py` | All `/cmd` dispatch |
| CLI presentation | `CLIView` | `agent/cli_view.py` | readline, progress, multiline |
| Session persistence | `AgentSession` | `agent/session.py` | sessions/messages SQLite |
| Configuration | `AgentConfig` | `agent/config.py` | 7 sub-configs, hot-reload |
| Memory services | `MemoryServices` | `agent/memory/` | Optional semantic memory layer |

---

## Session, SSE, and History Compression (Summary)

**Sessions:** Each REPL run creates a session row in SQLite. Messages are persisted per
turn. `/session load <id>` restores a previous conversation.

**SSE streaming:** LLM responses stream token-by-token via Server-Sent Events. `LLMClient`
handles reconnect (up to `sse_reconnect_max`), heartbeat timeout, and partial completions.

**History compression:** When `ctx.conv.history` exceeds `context_char_limit` (default
8000 chars), `HistoryManager.compress()` summarizes the oldest turns using the LLM.
The most recent `history_protect_turns` (default 2) turns are always protected.

---

## Slash Command Categories (Summary)

> **Keeping this list current:** When a new command is added, update both this summary AND the full reference table in [05_agent_07 §Slash Command Reference](05_agent_07_cli-and-commands.md). See [05_agent_07 §Maintaining the Command List](05_agent_07_cli-and-commands.md) for the complete procedure.

| Category | Commands |
|---|---|
| Session | `/session list\|load\|rename\|delete`, `/clear [new]`, `/undo`, `/history`, `/export` |
| MCP | `/mcp status` |
| Config / stats | `/config`, `/stats`, `/set`, `/reload` |
| Context | `/context`, `/compact`, `/system` |
| DB | `/db rag stats\|urls\|clean\|rebuild-fts\|vec-rebuild\|reconcile-url\|recover\|consistency; session stats\|health\|checkpoint\|vacuum\|purge\|recover` |
| Tool / plan | `/tool list\|show`, `/plan` |
| Workflow | `/approve [reason]`, `/reject [reason]` |
| Debug / audit | `/debug`, `/audit` |
| RAG / Export | `/rag search`, `/export`, `/compact` |
| Memory | `/memory list\|search\|show\|pin\|unpin\|delete\|prune\|status` |
| Other | `/help` |

---

## Major Constraints

| Constraint | Value |
|---|---|
| Max tool turns per message | `max_tool_turns` (default 5) |
| History compression threshold | `context_char_limit` (default 8000 chars) |
| HTTP timeout | `http_timeout` (default 30.0 sec) |
| LLM retry limit | `llm_max_retries` (default 3) |
| Tool result cache TTL | `tool_cache_ttl` (default 300 sec) |

---

## Related Chapters

| Topic | File |
|---|---|
| Runtime component architecture | [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md) |
| Turn processing flow | [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md) |
| State and persistence | [05_agent_04_state-and-persistence.md](05_agent_04_state-and-persistence.md) |
| LLM and streaming | [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) |
| Tool execution and approval | [05_agent_06_tool-execution-and-approval.md](05_agent_06_tool-execution-and-approval.md) |
| CLI and commands | [05_agent_07_cli-and-commands.md](05_agent_07_cli-and-commands.md) |
| Configuration | [05_agent_08_configuration.md](05_agent_08_configuration.md) |
| Data layer | [05_agent_09_data-layer.md](05_agent_09_data-layer.md) |
| Operations and observability | [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md) |
| Extension points | [05_agent_11_extension-points.md](05_agent_11_extension-points.md) |
| API reference | [05_agent_12_reference-api.md](05_agent_12_reference-api.md) |
