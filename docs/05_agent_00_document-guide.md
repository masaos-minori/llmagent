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

These files document the LLM Agent REPL system: a CLI tool that uses LLM function
calling to interact with MCP tool servers, maintain conversation history, and deliver
answers to the terminal. They are the primary reference (original monolithic source
files have been deleted).

---

## Recommended Reading Order (Human)

```
01 Overview → 02 Runtime Architecture → 03 Turn Processing Flow
  → 04 State/Persistence → 05 LLM/Streaming → 06 Tool Execution/Approval
  → 07 CLI/Commands → 08 Configuration → 09 Data Layer
  → 10 Operations/Observability → 11 Extension Points → 12 Memory → 13 Reference API
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What is the agent and how does it work? | `05_agent_01` |
| What are the major components/dependencies? Function signatures? | `05_agent_02` (runtime) / `05_agent_13` (signatures) |
| What happens during a single user turn? | `05_agent_03` (§Overview; §LLM+Tool Loop; §Workflow Engine) |
| History compression? What state is persisted vs in-memory? | `05_agent_04` |
| SSE streaming, retry, `LLMTransportError`? | `05_agent_05` |
| How are tools executed/approved? `/plan` mode? | `05_agent_06` (§Execution; §Approval) |
| Slash commands and effects? `/reload` scope? | `05_agent_07` (§Slash Commands; §Hot Reload) |
| Config fields, defaults, which file controls what? | `05_agent_08` (§Loading Agent Config; §LLM/RAG; §Tools/Memory; §MCP/Approval/Obs) |
| What SQLite tables does the agent use? | `05_agent_09_data-layer-*.md` (session-db / access-patterns) |
| How to start, verify, troubleshoot, read audit logs? | `05_agent_10_operations-and-observability-*.md` (startup-and-health / validation-and-troubleshooting / audit-and-otel) |
| How to add a plugin command, tool, or new MCP server? | `05_agent_11_extension-points-*.md` (plugin-command / tool-registration / registry-rules) |
| How does the memory layer work (injection, pruning)? | `05_agent_12_memory-*.md` (overview-and-modes / module-ref-retrieval-and-injection) — **Implemented** (SQLite + JSONL + FTS5 + optional vectors) |
| Where is class X defined and what are its callers? | `05_agent_13` (signatures, callers, callees) — runtime context → `05_agent_02` |

---

## Canonical Source Rules

Deleted `05_ref-*` / `05_agent-impl-flow.md` / `05_agent-ops.md` files are superseded by chapters 02–13 above. When in doubt, trust the restructured files. Known issues, spec conflicts, and open questions are consolidated in [05_agent_90_inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md).

---

## File Index

| Chapter | Files |
|---|---|
| 00 | [document-guide.md](05_agent_00_document-guide.md) — this file |
| 01 | [system-overview.md](05_agent_01_system-overview.md) — purpose, tool-calling model, component map |
| 02 | [runtime-architecture.md](05_agent_02_runtime-architecture.md) — dependency diagram, responsibilities |
| 03 turn processing | [overview](05_agent_03_turn-processing-flow-overview.md), [llm-tool-loop](05_agent_03_turn-processing-flow-llm-tool-loop.md), [workflow-engine](05_agent_03_turn-processing-flow-workflow-engine.md) |
| 04 state/persistence | [state-model](05_agent_04_state-and-persistence-state-model.md), [history-compression](05_agent_04_state-and-persistence-history-compression.md), [platform-databases](05_agent_04_state-and-persistence-platform-databases.md) |
| 05 | [llm-and-streaming.md](05_agent_05_llm-and-streaming.md) — LLMClient API, SSE, reconnect |
| 06 tool exec/approval | [execution](05_agent_06_tool-execution-and-approval-execution.md), [approval](05_agent_06_tool-execution-and-approval-approval.md), [concurrency-safety](05_agent_06_tool-execution-and-approval-concurrency-safety.md), [canonical](05_agent_06_tool-execution-and-approval-canonical.md) |
| 07 CLI/commands | [cli-reference](05_agent_07_cli-and-commands-cli-reference.md), [cliview](05_agent_07_cli-and-commands-cliview.md), [command-registry](05_agent_07_cli-and-commands-command-registry.md), [purpose](05_agent_07_cli-and-commands-purpose.md), [repl-io](05_agent_07_cli-and-commands-repl-io.md), [hot-reload](05_agent_07_cli-and-commands-hot-reload.md), [migration-notes](05_agent_07_cli-and-commands-migration-notes.md) |
| 07 slash commands | [session-mcp](05_agent_07_cli-and-commands-slash-commands-session-mcp.md), [context-db](05_agent_07_cli-and-commands-slash-commands-context-db.md), [workflow-debug](05_agent_07_cli-and-commands-slash-commands-workflow-debug.md), [memory-other](05_agent_07_cli-and-commands-slash-commands-memory-other.md) |
| 08 configuration | [loading-agent-config](05_agent_08_configuration-loading-agent-config.md), [llm-rag](05_agent_08_configuration-llm-rag.md), [tools-memory](05_agent_08_configuration-tools-memory.md), [mcp-approval-obs](05_agent_08_configuration-mcp-approval-obs.md) |
| 09 data layer | [session-db](05_agent_09_data-layer-session-db.md), [access-patterns](05_agent_09_data-layer-access-patterns.md), [indexing-boundaries](05_agent_09_data-layer-indexing-boundaries.md) |
| 10 operations | [startup-and-health](05_agent_10_operations-and-observability-startup-and-health.md), [audit-and-otel](05_agent_10_operations-and-observability-audit-and-otel.md), [workflow-observability](05_agent_10_operations-and-observability-workflow-observability.md), [validation-and-troubleshooting](05_agent_10_operations-and-observability-validation-and-troubleshooting.md), [monitoring](05_agent_10_operations-and-observability-monitoring.md), [rag-diagnostics-and-memory](05_agent_10_operations-and-observability-rag-diagnostics-and-memory.md) |
| 11 extension points | [plugin-command](05_agent_11_extension-points-plugin-command.md), [tool-registration](05_agent_11_extension-points-tool-registration.md), [registry-rules](05_agent_11_extension-points-registry-rules.md) |
| 12 memory | [overview-and-modes](05_agent_12_memory-overview-and-modes.md), [gate-data-model-search](05_agent_12_memory-gate-data-model-search.md), [module-ref-core-and-store](05_agent_12_memory-module-ref-core-and-store.md), [module-ref-retrieval-and-injection](05_agent_12_memory-module-ref-retrieval-and-injection.md), [module-ref-extraction-and-facade](05_agent_12_memory-module-ref-extraction-and-facade.md), [module-ref-ops-and-scoring](05_agent_12_memory-module-ref-ops-and-scoring.md) |
| 13 | [reference-api.md](05_agent_13_reference-api.md) — per-module API: role, callers, callees, config, failure |
| 90 | [inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md) — known bugs, spec conflicts, open questions |

---

## Documentation Consistency Checklist

When changing schema or command references, verify: `05_agent_01_system-overview.md` §Slash Commands and `05_agent_07_cli-and-commands-*.md` match `scripts/agent/commands/registry.py` (every CommandDef has a doc entry, no deleted commands referenced); `05_agent_09_data-layer-*.md` matches `scripts/db/schema_sql.py` and `init_db.sh`; diagnostics docs reference `session_diagnostics` only (no deleted `diagnostics.jsonl`).

---

## Known Limitations

Old monolithic source files (`05_agent.md`, `05_ref-agent-*.md`, etc.) have been deleted; this document set is the primary reference. Memory layer (`agent/memory/`) is documented in `05_agent_12_memory-*.md` and summarized in `05_agent_02` §Memory Services.

## Related Documents

- `05_agent_01_system-overview.md`
- `05_agent_02_runtime-architecture.md`
- `05_agent_05_llm-and-streaming.md`
- `05_agent_13_reference-api.md`
- `05_agent_90_inconsistencies_and_known_issues.md`

## Keywords

agent
documentation
guide
routing
file-index
