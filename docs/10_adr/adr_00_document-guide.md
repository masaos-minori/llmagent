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
  - ADR-015-reference-document-class-disposition.md
---
# ADR: Document Guide

## Purpose

This directory contains all Architecture Decision Records (ADRs). Each ADR captures a significant architectural decision with its context, options considered, and rationale.

## Known Deviations

No confirmed deviations.

## Reading Order

| Category | File |
|---|---|
| ADR Index | `adr-index.md` |
| Workflow Engine Mandatory | `ADR-001-workflow-engine-mandatory.md` |
| Config Isolation | `ADR-002-config-isolation.md` |
| Tool Registry Authority | `ADR-003-runtime-tool-registry-routing-authority.md` |
| Environment Failure Handling | `ADR-004-environment-failure-handling-policy.md` |
| ADR-002 Supporting Sections (companion) | `adr_02_config-isolation-supporting-sections.md` |
| ADR-003 Supporting Sections (companion) | `adr_03_runtime-tool-registry-supporting-sections.md` |
| ADR-004 Supporting Sections (companion) | `adr_04_failure-handling-supporting-sections.md` |
| RAG Source-Derived Index | `ADR-005-rag-source-derived-index-relationships.md` |
| EventBus Persistence & SSE | `ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md` |
| HTTP MCP Adoption | `ADR-007-http-mcp-adoption-and-stdio-non-support.md` |
| SQLite 4DB Separation | `ADR-008-sqlite-4db-separation.md` |
| ADR-008 Supporting Sections (companion) | `adr_08_sqlite-4db-supporting-sections.md` |
| RAG FT5 Text Separation | `ADR-009-rag-ft5-text-separation.md` |
| RAG Fallback | `ADR-010-rag-fallback.md` |
| Git MCP Server-Side Write | `ADR-012-git-mcp-server-side-write-enforcement.md` |
| EventBus Authentication | `ADR-013-eventbus-authentication-authorization.md` |
| Agent Control Plane Boundaries | `ADR-014-agent-control-plane-responsibility-boundaries.md` |
| Reference Document Class Disposition | `ADR-015-reference-document-class-disposition.md` |

## AI Query Routing

| Question | Rule |
|---|---|
| Architectural decisions & rationale | Any `ADR-NNN` file |
| ADR status & dependencies | `adr-index.md` |
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
