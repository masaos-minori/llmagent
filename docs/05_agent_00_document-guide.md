---
title: "Agent Documentation Guide"
area: agent
tags:
  - agent
  - documentation
  - guide
  - routing
related:
  - 05_agent_01_system-overview.md
  - 05_agent_02_runtime-architecture.md
  - 05_agent_05_llm-and-streaming.md
  - 05_agent_13_reference-api.md
  - 05_agent_90_inconsistencies_and_known_issues.md
---

# Agent Documentation Guide

## Purpose

This document is the entry point for the restructured Agent documentation set. It guides readers to the right chapter based on their concern, not by listing every file.

## Design Intent

The value of this document is navigation logic — human-curated guidance on which chapter addresses which question. Mechanical inventories (file lists, keyword enumerations, implementation-diff-memo-style notes) are delegated to code search via the Canonical Source Rule.

## Responsibility Boundary

- **In scope**: Chapter structure overview, question-to-chapter navigation mapping, Canonical Source Rule definition, handling of Known Issues / Deprecated Items / Needs Confirmation entries.
- **Out of scope**: Detailed file indexes, keyword lists duplicatable by code search, implementation diff memos ("confirmed at file X line Y").

## Key Constraints

- When a fact is mechanically derivable from code, point to the source rather than transcribing it.
- Unrecoverable design rationales must be explicitly marked `Needs Confirmation` rather than silently dropped.
- Do not modify other documents in the `05_agent_*.md` set.
- Do not add new content beyond what exists in the current document.
- Do not change the doc set directory structure.

## Operational Notes

- Recommended reading order for humans: Overview → Runtime Architecture → Turn Processing Flow → State/Persistence → LLM/Streaming → Tool Execution/Approval → CLI/Commands → Configuration → Data Layer → Operations/Observability → Extension Points → Memory → Reference API.
- The canonical query routing table maps questions to chapters; use it to find the right chapter before searching code.

## Known Limitations

- [NC-001](00_governance_03_issue-and-uncertainty-management.md): UTF8_PARTIAL_DECODE_ERROR and PREMATURE_EOF distinction
- [NC-004](00_governance_03_issue-and-uncertainty-management.md): Distance measurement cosine/L2 determination impossibility

## Related Docs

### Governance
- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

### Related ADRs
- [ADR-001](adr/ADR-001-workflow-engine-mandatory.md) — Workflow Engine必須化
- [ADR-003](adr/ADR-003-runtime-tool-registry-routing-authority.md) — RuntimeToolRegistryを唯一のルーティング権威とする
- [ADR-004](adr/ADR-004-environment-profile-fail-fast-fail-open.md) — Environment Profile別障害方針 — Fail-Fast/Fail-Open
- [ADR-007](adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md) — HTTP MCP採用とstdio非サポート
- [ADR-013](adr/ADR-013-mcp-tool-availability-model.md) — MCP Tool Availability Model

### Query Routing Table

| Question | File |
|---|---|
| What is the agent? Major components/deps, function signatures | `05_agent_01` / `05_agent_02` / `05_agent_13` |
| 1-user-turn flow, history compression, persistence vs memory state | `05_agent_03` / `05_agent_04` |
| SSE streaming, retry, `LLMTransportError` | `05_agent_05` |
| Tool execution/approval, `/plan` mode, slash commands, `/reload` | `05_agent_06` / `05_agent_07` |
| Config fields, defaults, control files | `05_agent_08` |
| SQLite tables used, startup/validation/troubleshooting, audit log | `05_agent_09` / `05_agent_10` |
| Adding a new MCP server | `04_mcp_06_15` |
| Memory layer | `05_agent_12` |
| Where is class X defined and who calls it | `05_agent_13` → `05_agent_02` |

### Consistency Checklist

When schema/command references change, verify that `05_agent_01_system-overview.md` Slash Commands and `05_agent_07_cli-and-commands-*.md` match `scripts/agent/commands/registry.py` (CommandDef per documented item, no deleted command references), `05_agent_09_data-layer-*.md` matches `scripts/db/schema_sql.py`/`init_db.sh`, and diagnostic docs reference only `session_diagnostics` (no references to deleted `diagnostics.jsonl`).

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
| 07 | CLI/commands — CLI reference, CLIView, command registry, purpose, REPL I/O, hot-reload, migration notes |
| 08 | Configuration — loading agent config, LLM/RAG, tools/memory, MCP/approval/observability |
| 09 | Data layer — session DB, access patterns, indexing boundaries |
| 10 | Operations — startup/health, audit/OTel, workflow observability, validation/troubleshooting, monitoring, RAG diagnostics/memory |
| 12 | Memory — overview/modes, gate/data-model/search, module refs (core/store, retrieval/injection, extraction/facade, ops/scoring) |
| 13 | Reference API — per-module API: role, callers, callees, config, failure |
| 90 | Inconsistencies and known issues — known bugs, spec conflicts, open questions |

### Removed Files

Deleted `05_ref-*` / `05_agent-impl-flow.md` / `05_agent-ops.md` files are integrated into chapters 02-13 above. See [05_agent_90_inconsistencies_and_known_issues.md](05_agent_90_inconsistencies_and_known_issues.md) for known issues and unresolved items.

### Additional References

- `05_agent_01_system-overview.md`
- `05_agent_02_runtime-architecture.md`
- `05_agent_05_llm-and-streaming.md`
- `05_agent_13_reference-api.md`
- `05_agent_90_inconsistencies_and_known_issues.md`
