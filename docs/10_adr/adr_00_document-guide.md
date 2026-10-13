---
title: "ADR: Document Guide"
area: governance
tags:
  - governance
  - adr
  - document-guide
related:
  - 00_index.md
  - overview_00_document-guide.md
  - adr_02_015_reference-document-class-disposition.md
  - governance_01_documentation-policy.md
---
# ADR: Document Guide

## Purpose

This directory contains all Architecture Decision Records (ADRs). Each ADR captures a significant architectural decision with its context, options considered, and rationale.

## Known Deviations

No confirmed deviations.

## Reading Order

| Category | File |
|---|---|
| ADR Index | `adr_01_index.md` |
| Workflow Engine Mandatory | `adr_02_001_workflow-engine-mandatory.md` |
| Config Isolation | `adr_02_002_config-isolation.md` |
| Tool Registry Authority | `adr_02_003_runtime-tool-registry-routing-authority.md` |
| Environment Failure Handling | `adr_02_004_environment-failure-handling-policy.md` |
| RAG Source-Derived Index | `adr_02_005_rag-source-derived-index-relationships.md` |
| EventBus Persistence & SSE | `adr_02_006_eventbus-sqlite-persistence-and-sse-delivery.md` |
| HTTP MCP Adoption | `adr_02_007_http-mcp-adoption-and-stdio-non-support.md` |
| SQLite 4DB Separation | `adr_02_008_sqlite-4db-separation.md` |
| RAG FTS5 Text Separation | `adr_02_009_rag-fts5-text-separation.md` |
| RAG Fallback | `adr_02_010_rag-fallback.md` |
| Git MCP Server-Side Write | `adr_02_012_git-mcp-server-side-write-enforcement.md` |
| EventBus Authentication | `adr_02_013_eventbus-authentication-authorization.md` |
| Agent Control Plane Boundaries | `adr_02_014_agent-control-plane-responsibility-boundaries.md` |
| Reference Document Class Disposition | `adr_02_015_reference-document-class-disposition.md` |

## File Naming

Files in this directory follow `adr_NN_<name>.md`: `adr_00_` is this guide, `adr_01_` is the index, and each ADR is `adr_02_<NNN>_<slug>.md` where `<NNN>` is the three-digit ADR number. The ADR ID in text (for example `ADR-006`) is unchanged.

## AI Query Routing

| Question | Rule |
|---|---|
| Architectural decisions & rationale | Any `ADR-NNN` file |
| ADR status & dependencies | `adr_01_index.md` |
| Documentation policy for ADRs | `governance_01_documentation-policy.md` |

## Canonical Sources

See [Documentation Policy](../00_governance/governance_01_documentation-policy.md) for ADR naming conventions, status definitions, and section header rules.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md`. Do not duplicate them in individual chapters.

## Reference API

No reference APIs exist in this directory. All files are ADR documents.

## Keywords

- adr
- architecture-decision-record
- document-guide
- reading-order
- decision-rationale
