---
title: "Agent Documentation Guide"
area: agent
tags:
  - agent
  - documentation
  - guide
  - routing
related:
  - agent_01_system-overview.md
  - agent_02_runtime-architecture.md
  - agent_05_llm-and-streaming.md
  - agent_12_reference-api.md
  - governance_03_issue-and-uncertainty-management.md
  - governance_01_documentation-policy.md
  - governance_02_documentation-metadata.md
  - governance_04_documentation-checks.md
  - ADR-001-workflow-engine-mandatory.md
  - ADR-003-runtime-tool-registry-routing-authority.md
  - ADR-004-environment-failure-handling-policy.md
  - ADR-007-http-mcp-adoption-and-stdio-non-support.md
---

# Agent Documentation Guide

## Purpose

This document is the entry point for the restructured Agent documentation set. It guides readers to the right chapter based on their concern, not by listing every file.

## Design Intent

The value of this document is navigation logic — human-curated guidance on which chapter addresses which question. Mechanical inventories (file lists, keyword enumerations, implementation-diff-memo-style notes) are delegated to code search via the Canonical Source Rule.

## Responsibility Boundary

- **In scope**: Chapter structure overview, question-to-chapter navigation mapping, Canonical Source Rule definition, handling of Known Issues / Deprecated Items here; uncertainty items tracked per [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md).
- **Out of scope**: Detailed file indexes, keyword lists duplicatable by code search, implementation diff memos ("confirmed at file X line Y").

## Key Constraints

- When a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must not be silently dropped; their disposition follows [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md).
- Changes to the doc set directory structure must go through the governance process.

## Operational Notes

- Recommended reading order for humans: Overview → Runtime Architecture → Turn Processing Flow → State/Persistence → LLM/Streaming → Tool Execution/Approval → CLI/Commands → Configuration → Data Layer → Operations/Observability → Memory → Reference API.
- The canonical query routing table maps questions to chapters; use it to find the right chapter before searching code.

## Navigation Guide

### Governance
- [Documentation Policy](../00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](../00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](../00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](../00_governance/governance_04_documentation-checks.md)

### Related ADRs
- [ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md) — Mandatory Workflow Engine
- [ADR-003](../10_adr/ADR-003-runtime-tool-registry-routing-authority.md) — RuntimeToolRegistry as the Sole Routing Authority
- [ADR-004](../10_adr/ADR-004-environment-failure-handling-policy.md) — Failure Handling Policy Across Environments
- [ADR-007](../10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md) — Adoption of HTTP MCP and Non-Support of stdio

### Query Routing Table

| Question | File |
|---|---|
| What is the agent? Major components/deps, function signatures | `agent_01` / `agent_02` / `agent_12` |
| 1-user-turn flow, history compression, persistence vs memory state | `agent_03` / `agent_04` |
| SSE streaming, retry, `LLMTransportError` | `agent_05` |
| Tool execution/approval, `/plan` mode, slash commands, `/reload` | `agent_06` / `agent_07` |
| Config fields, defaults, control files | `agent_08` |
| SQLite tables used, startup/validation/troubleshooting, audit log | `agent_09` / `agent_10` |
| Adding a new MCP server | `mcp_06_12` |
| Memory layer | `agent_11` |
| Where is class X defined and who calls it | `agent_12` → `agent_02` |

### Consistency Checklist

When schema/command references change, verify that `agent_07_cli-and-commands-*.md` matches `scripts/agent/commands/command_defs_list.py` (`_COMMANDS`; no deleted command references), `agent_09_data-layer-*.md` matches `scripts/db/schema_sql.py`/`init_db.sh`, and diagnostic docs reference only `session_diagnostics` (no references to deleted `diagnostics.jsonl`).

### Document Set Chapters

| Chapter | Content |
|---|---|
| 00 | This file |
| 01 | System overview — purpose, tool-calling model, component map |
| 02 | Runtime architecture — dependency diagram, responsibilities |
| 03 | Turn processing flow — overview, LLM-tool loop, workflow engine |
| 04 | State/persistence — state model, history compression, platform databases |
| 05 | LLM/streaming — LLMClient API, SSE, reconnect |
| 06 | Tool exec/approval — execution, approval, concurrency safety, canonical |
| 07 | CLI/commands — CLI reference, CLIView, command registry, purpose, REPL I/O, hot-reload, slash commands |
| 08 | Configuration — loading agent config, LLM/RAG, tools/memory, MCP/approval/observability |
| 09 | Data layer — session DB, access patterns, indexing boundaries |
| 10 | Operations — startup/health, audit/OTel, workflow observability, validation/troubleshooting, monitoring, RAG diagnostics/memory |
| 11 | Memory — overview/modes, gate/data-model/search, module refs (core/store, retrieval/injection, extraction/facade, ops/scoring) |
| 12 | Reference API — per-module API: role, callers, callees, config, failure |
| 13 | Reference API (generated) — class/function index generated from code |

### Additional References

- `agent_01_system-overview.md`
- `agent_02_runtime-architecture.md`
- `agent_05_llm-and-streaming.md`
- `agent_12_reference-api.md`
- `governance_03_issue-and-uncertainty-management.md`

## Keywords

- agent
- documentation
- guide
- routing
