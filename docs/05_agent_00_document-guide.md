# Agent Documentation Guide

Entry point for the restructured Agent documentation set.
Read this file first to choose which chapter to open.

---

## Purpose of This Document Set

These 13 files document the LLM Agent REPL system: a CLI tool that uses LLM function
calling to interact with MCP tool servers, maintain conversation history, and deliver
answers to the terminal.

They replace the original 12 source files (`05_agent.md`, `05_agent-impl-*.md`,
`05_ref-agent-*.md`, `05_agent-ops.md`) as the primary reference. Source files are
retained unchanged.

---

## Recommended Reading Order (Human)

```
01 System Overview              — start here for the big picture
    ↓
02 Runtime Architecture         — component map and dependency relationships
    ↓
03 Turn Processing Flow         — one turn from input to answer
    ↓
04 State and Persistence        — what is stored, where, and when
    ↓
05 LLM and Streaming            — SSE, reconnect, partial completion
    ↓
06 Tool Execution and Approval  — routing, safety controls, approval flow
    ↓
07 CLI and Commands             — all slash commands with side effects
    ↓
08 Configuration                — all 7 sub-configs and their fields
    ↓
09 Data Layer                   — SQLite schemas and ownership boundaries
    ↓
10 Operations and Observability — startup, health checks, audit logs, OTel
    ↓
11 Extension Points             — plugins, @register_*, new MCP servers
    ↓
12 Reference API                — concise per-module API with cross-references
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What is the agent and how does it work? | `05_agent_01` |
| What are the major components and dependencies? | `05_agent_02` |
| What happens during a single user turn? | `05_agent_03` |
| How does history compression work? | `05_agent_04` |
| What state is persisted vs in-memory? | `05_agent_04` |
| How does SSE streaming and retry work? | `05_agent_05` |
| What is `LLMTransportError`? | `05_agent_05` |
| How are tools executed and approved? | `05_agent_06` |
| What is the approval flow for destructive tools? | `05_agent_06` |
| What does `/plan` mode do? | `05_agent_06` |
| What are all the slash commands and their effects? | `05_agent_07` |
| What does `/reload` apply vs what requires restart? | `05_agent_07` |
| What are all config fields and defaults? | `05_agent_08` |
| What config file controls what behavior? | `05_agent_08` |
| What SQLite tables does the agent use? | `05_agent_09` |
| How to start, verify, and troubleshoot the agent? | `05_agent_10` |
| How to read audit logs? | `05_agent_10` |
| How to add a plugin command or tool? | `05_agent_11` |
| How to add a new MCP server? | `05_agent_11` |
| Where is class X defined and what are its callers? | `05_agent_12` |

---

## Canonical Source Rules

- `05_ref-*` files were canonical for API details. Content now lives in chapters 02–12.
- `05_agent-impl-flow.md` was canonical for turn flow. Content now lives in chapter 03.
- `05_agent-ops.md` was canonical for operations. Content now lives in chapter 10.
- When old files and new files disagree, trust the new restructured files.
- `05_ref-agent-repl.md` note on `repl_tool_exec.py` deletion is authoritative.

---

## Spec Conflicts and Open Questions

| Issue | Location |
|---|---|
| `repl_tool_exec.py` deletion (tool logic moved to `ToolExecutor`) | [02 §Spec Conflict](05_agent_02_runtime-architecture.md) |
| `ServerLifecycleManager` deletion (`_ServerLifecycleRouter` in factory.py) | [02 §Spec Conflict](05_agent_02_runtime-architecture.md) |
| `AgentSession` owning RAG table access (responsibility boundary) | [12 §AgentSession](05_agent_12_reference-api.md) |
| Workflow engine fallback conditions | [03 §WorkflowEngine](05_agent_03_turn-processing-flow.md) |

---

## File Index

| File | Description |
|---|---|
| [05_agent_01_system-overview.md](05_agent_01_system-overview.md) | Purpose, entry point, tool-calling model, component map, constraints |
| [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md) | Component dependency diagram, responsibility breakdown, spec conflicts |
| [05_agent_03_turn-processing-flow.md](05_agent_03_turn-processing-flow.md) | Full one-turn sequence, memory injection, compression, LLM loop, error handling |
| [05_agent_04_state-and-persistence.md](05_agent_04_state-and-persistence.md) | AgentContext state model, session persistence, HistoryManager, data classification |
| [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) | LLMClient API, SSE streaming, reconnect, partial completion, usage collection |
| [05_agent_06_tool-execution-and-approval.md](05_agent_06_tool-execution-and-approval.md) | ToolExecutor, parallel/serial execution, approval flow, plan mode, cache, safety |
| [05_agent_07_cli-and-commands.md](05_agent_07_cli-and-commands.md) | CLIView, all slash commands with side effects and related state |
| [05_agent_08_configuration.md](05_agent_08_configuration.md) | All 7 AgentConfig sub-configs: fields, defaults, validation, hot-reload scope |
| [05_agent_09_data-layer.md](05_agent_09_data-layer.md) | SQLite schemas (session/rag/workflow), ownership boundaries, FTS5 |
| [05_agent_10_operations-and-observability.md](05_agent_10_operations-and-observability.md) | Startup, verification, audit log, OTel, /context, /stats, troubleshooting |
| [05_agent_11_extension-points.md](05_agent_11_extension-points.md) | Plugin architecture, @register_command/tool/pipeline_stage, new MCP server |
| [05_agent_12_reference-api.md](05_agent_12_reference-api.md) | Concise per-module API: role, callers, callees, config, failure |

---

## Known Limitations

- `routing.md` entries for the old `05_*` files will be updated as part of this task.
- Old source files (`05_agent.md`, `05_ref-agent-*.md`, etc.) are retained unchanged.
  This document set supersedes them as the primary reference.
- Memory layer documentation (`agent/memory/`) is summarized only; detailed API
  is in `docs/05_ref-agent-context.md` (retained source file).
