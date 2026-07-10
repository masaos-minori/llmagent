---
title: "Agent Documentation Guide"
category: agent
tags:
  - agent
  - documentation
  - guide
  - routing
  - file-index
related:
  - 05_agent_01_system-overview.md
  - 05_agent_02_runtime-architecture.md
  - 05_agent_05_llm-and-streaming.md
  - 05_agent_13_reference-api.md
  - 05_agent_90_inconsistencies_and_known_issues.md
---

# Agent Documentation Guide

Entry point for the restructured Agent documentation set.
Read this file first to choose which chapter to open.

---

## Purpose of This Document Set

These 14 files document the LLM Agent REPL system: a CLI tool that uses LLM function
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
12 Memory                       — memory layer, injection, pruning, embeddings
    ↓
13 Reference API                — concise per-module API with cross-references
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What is the agent and how does it work? | `05_agent_01` |
| What are the major components and dependencies? | `05_agent_02` (runtime behavior, data flow) — for function signatures → `05_agent_13` |
| What happens during a single user turn? | `05_agent_03` (§Overview; §LLM+Tool Loop; §Workflow Engine) |
| How does history compression work? | `05_agent_04` (§History Compression) |
| What state is persisted vs in-memory? | `05_agent_04` (§State Model) |
| How does SSE streaming and retry work? | `05_agent_05` |
| What is `LLMTransportError`? | `05_agent_05` |
| How are tools executed and approved? | `05_agent_06` (§Execution; §Approval) |
| What is the approval flow for destructive tools? | `05_agent_06` (§Approval) |
| What does `/plan` mode do? | `05_agent_06` (§Approval) |
| What are all the slash commands and their effects? | `05_agent_07` (§Slash Commands) |
| What does `/reload` apply vs what requires restart? | `05_agent_07` (§Hot Reload) |
| What are all config fields and defaults? | `05_agent_08` (§Loading Agent Config; §LLM/RAG; §Tools/Memory; §MCP/Approval/Obs) |
| What config file controls what behavior? | `05_agent_08` (§Loading Agent Config) |
| What SQLite tables does the agent use? | `05_agent_09` (§Session DB; §Access Patterns) |
| How to start, verify, and troubleshoot the agent? | `05_agent_10` (§Startup Health; §Troubleshooting) |
| How to read audit logs? | `05_agent_10` (§Audit OTel) |
| How to add a plugin command or tool? | `05_agent_11` (§Plugin Command; §Tool Registration) |
| How to add a new MCP server? | `05_agent_11` (§Registry Rules) |
| How does the memory layer work (injection, pruning)? | `05_agent_12` (§Overview Memory Modes; §Module Ref Core Types; §Module Ref Store CRUD) — **Implemented** (SQLite + JSONL + FTS5 + optional vector embedding) |
| Where is class X defined and what are its callers? | `05_agent_13` (function signatures, callers, callees) — for runtime context → `05_agent_02` |

---

## Canonical Source Rules

- `05_ref-*` files were canonical for API details. Content now lives in chapters 02–13.
- `05_agent-impl-flow.md` was canonical for turn flow. Content now lives in chapter 03.
- `05_agent-ops.md` was canonical for operations. Content now lives in chapter 10.
- When old files and new files disagree, trust the new restructured files.

---

## Spec Conflicts and Open Questions

All known issues, spec conflicts, and open questions are consolidated in
[05_agent_90_inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md).

| Issue | ID |
|---|---|


---

## File Index

| File | Description |
|---|---|
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | Entry point |
| [05_agent_01_system-overview.md](05_agent_01_system-overview.md) | Purpose, entry point, tool-calling model, component map, constraints |
| [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md) | Component dependency diagram, responsibility breakdown, spec conflicts |
| [05_agent_03_turn-processing-flow-overview.md](05_agent_03_turn-processing-flow-overview.md) | One-turn processing flow, memory injection, history compression |
| [05_agent_03_turn-processing-flow-llm-tool-loop.md](05_agent_03_turn-processing-flow-llm-tool-loop.md) | LLM invocation, tool loop, error handling |
| [05_agent_03_turn-processing-flow-workflow-engine.md](05_agent_03_turn-processing-flow-workflow-engine.md) | WorkflowEngine integration, partial completion, state changes |
| [05_agent_04_state-and-persistence-state-model.md](05_agent_04_state-and-persistence-state-model.md) | AgentContext state model, session persistence |
| [05_agent_04_state-and-persistence-history-compression.md](05_agent_04_state-and-persistence-history-compression.md) | History compression, conversation history, data classification |
| [05_agent_04_state-and-persistence-platform-databases.md](05_agent_04_state-and-persistence-platform-databases.md) | Platform databases, session/RAG boundary |
| [05_agent_05_llm-and-streaming.md](05_agent_05_llm-and-streaming.md) | LLMClient API, SSE streaming, reconnect, partial completion, usage collection |
| [05_agent_06_tool-execution-and-approval-execution.md](05_agent_06_tool-execution-and-approval-execution.md) | ToolExecutor, parallel/serial execution, DAG scheduler |
| [05_agent_06_tool-execution-and-approval-approval.md](05_agent_06_tool-execution-and-approval-approval.md) | Approval flow, plan mode, safety controls |
| [05_agent_06_tool-execution-and-approval-concurrency-safety.md](05_agent_06_tool-execution-and-approval-concurrency-safety.md) | ToolLoopGuard, concurrency limits, fail-closed policy |
| [05_agent_06_tool-execution-and-approval-canonical.md](05_agent_06_tool-execution-and-approval-canonical.md) | Canonical approval model, partial completion persistence |
| [05_agent_07_cli-and-commands-cli-reference.md](05_agent_07_cli-and-commands-cli-reference.md) | CLIView, CommandRegistry |
| [05_agent_07_cli-and-commands-cliview.md](05_agent_07_cli-and-commands-cliview.md) | CLIView callbacks and methods |
| [05_agent_07_cli-and-commands-command-registry.md](05_agent_07_cli-and-commands-command-registry.md) | CommandRegistry dispatch logic |
| [05_agent_07_cli-and-commands-purpose.md](05_agent_07_cli-and-commands-purpose.md) | Purpose |
| [05_agent_07_cli-and-commands-repl-io.md](05_agent_07_cli-and-commands-repl-io.md) | REPL input/output model |
| [05_agent_07_cli-and-commands-slash-commands-session-mcp.md](05_agent_07_cli-and-commands-slash-commands-session-mcp.md) | Slash commands: Session, MCP, Config/stats categories |
| [05_agent_07_cli-and-commands-slash-commands-context-db.md](05_agent_07_cli-and-commands-slash-commands-context-db.md) | Slash commands: Context, DB, Plan categories |
| [05_agent_07_cli-and-commands-slash-commands-workflow-debug.md](05_agent_07_cli-and-commands-slash-commands-workflow-debug.md) | Slash commands: Workflow, Debug/audit, RAG/Export categories |
| [05_agent_07_cli-and-commands-slash-commands-memory-other.md](05_agent_07_cli-and-commands-slash-commands-memory-other.md) | Slash commands: Memory, MDQ, Plugin, Other categories |
| [05_agent_07_cli-and-commands-hot-reload.md](05_agent_07_cli-and-commands-hot-reload.md) | Hot-reload scope (/reload) |
| [05_agent_07_cli-and-commands-migration-notes.md](05_agent_07_cli-and-commands-migration-notes.md) | Migration notes |
| [05_agent_08_configuration-loading-agent-config.md](05_agent_08_configuration-loading-agent-config.md) | Configuration loading, AgentConfig structure |
| [05_agent_08_configuration-llm-rag.md](05_agent_08_configuration-llm-rag.md) | LLMConfig, RAGConfig |
| [05_agent_08_configuration-tools-memory.md](05_agent_08_configuration-tools-memory.md) | ToolConfig, MemoryConfig |
| [05_agent_08_configuration-mcp-approval-obs.md](05_agent_08_configuration-mcp-approval-obs.md) | MCPConfig, ApprovalConfig, ObservabilityConfig |
| [05_agent_09_data-layer-session-db.md](05_agent_09_data-layer-session-db.md) | SQLite databases, session.sqlite tables |
| [05_agent_09_data-layer-access-patterns.md](05_agent_09_data-layer-access-patterns.md) | rag.sqlite tables, RAG MCP path, access patterns, memory tables |
| [05_agent_09_data-layer-indexing-boundaries.md](05_agent_09_data-layer-indexing-boundaries.md) | Context manager pattern, FTS5 index, workflow SQLite, persistence boundaries |
| [05_agent_10_operations-and-observability-startup-health.md](05_agent_10_operations-and-observability-startup-health.md) | Startup procedure, operational verification |
| [05_agent_10_operations-and-observability-audit-otel.md](05_agent_10_operations-and-observability-audit-otel.md) | Health probes, audit log |
| [05_agent_10_operations-and-observability-workflow.md](05_agent_10_operations-and-observability-workflow.md) | OpenTelemetry, workflow observability, startup validation |
| [05_agent_10_operations-and-observability-diagnostics.md](05_agent_10_operations-and-observability-diagnostics.md) | MCP reload semantics, /context, /stats, partial completion monitoring |
| [05_agent_10_operations-and-observability-troubleshooting-runtime.md](05_agent_10_operations-and-observability-troubleshooting-runtime.md) | Troubleshooting, runtime diagnostics |
| [05_agent_10_operations-and-observability-rag-memory-shutdown.md](05_agent_10_operations-and-observability-rag-memory-shutdown.md) | RAG pipeline diagnostics, memory status, graceful shutdown |
| [05_agent_11_extension-points-plugin-command.md](05_agent_11_extension-points-plugin-command.md) | Plugin architecture, @register_command |
| [05_agent_11_extension-points-tool-registration.md](05_agent_11_extension-points-tool-registration.md) | @register_tool, @register_pipeline_stage |
| [05_agent_11_extension-points-registry-rules.md](05_agent_11_extension-points-registry-rules.md) | Registry API, extension rules, adding new MCP server |
| [05_agent_12_memory-overview-purpose.md](05_agent_12_memory-overview-purpose.md) | Persistent semantic memory overview, production checklist, purpose |
| [05_agent_12_memory-overview-memory-modes.md](05_agent_12_memory-overview-memory-modes.md) | Overview, memory modes |
| [05_agent_12_memory-gate-data-model-search.md](05_agent_12_memory-gate-data-model-search.md) | Activation gate, data model, JSONL format, search strategies |
| [05_agent_12_memory-module-ref-core-types.md](05_agent_12_memory-module-ref-core-types.md) | Module reference: types.py, enums.py, exceptions.py, models.py |
| [05_agent_12_memory-module-ref-store-crud.md](05_agent_12_memory-module-ref-store-crud.md) | Module reference: store.py, retriever.py, injection.py, ingestion.py, extract.py, jsonl_store.py, embedding_client.py |
| [05_agent_12_memory-module-ref-client-facade.md](05_agent_12_memory-module-ref-client-facade.md) | Module reference: services.py, mapper.py, write_ops.py, pin_ops.py |
| [05_agent_12_memory-module-ref-retrieval-search.md](05_agent_12_memory-module-ref-retrieval-search.md) | Module reference: count_ops.py, rebuild_ops.py, import_ops.py, scoring.py, rrf.py |
| [05_agent_12_memory-module-ref-ingestion-lifecycle.md](05_agent_12_memory-module-ref-ingestion-lifecycle.md) | Module reference: fts_query.py, sql_constants.py |
| [05_agent_12_memory-disabled-related.md](05_agent_12_memory-disabled-related.md) | Disabled behavior, related documents |
| [05_agent_13_reference-api.md](05_agent_13_reference-api.md) | Concise per-module API: role, callers, callees, config, failure |
| [05_agent_90_inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md) | Known bugs, spec conflicts, open questions, undocumented areas |

---

## Documentation Consistency Checklist

When making changes that affect schema or command references, verify the following:

### Command reference checks
- [ ] Update `05_agent_01_system-overview.md` (§Slash Commands)
- [ ] Update `05_agent_07_cli-and-commands.md` (tables, descriptions, scope notes)
- [ ] Compare against `scripts/agent/commands/registry.py` — every CommandDef should have a doc entry
- [ ] Verify no references to deleted commands (/mcp install, /note, /ingest, /debug audit, /db aliases) remain

### Schema checks
- [ ] Update `05_agent_09_data-layer.md` (table list, column descriptions)
- [ ] Compare against `scripts/db/schema_sql.py` — every table in schema should be documented
- [ ] Compare against `init_db.sh` — verify init logic matches schema docs

### Diagnostics checks
- [ ] Verify `session_diagnostics` only (no references to deleted diagnostics.jsonl)
- [ ] Verify SQL query examples match actual table columns
- [ ] Confirm operations doc (§Reading diagnostics) has all query patterns

---

## Known Limitations

- Old source files (`05_agent.md`, `05_ref-agent-*.md`, etc.) have been deleted.
  This document set is the primary reference.
- Memory layer (`agent/memory/`) is documented in `05_agent_12_memory.md` and summarized in `05_agent_02` §Memory Services.

## Related Documents

- `agent`
- `documentation`
- `guide`

## Keywords

agent
documentation
guide
routing
file-index
