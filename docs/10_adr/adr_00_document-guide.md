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
  - adr_02_07_015_docs-reference-document-class-disposition.md
  - governance_01_documentation-policy.md
---
# ADR: Document Guide

## Purpose

This directory contains all Architecture Decision Records (ADRs). Each ADR captures a significant architectural decision with its context, options considered, and rationale.

## Known Deviations

Confirmed deviations are tracked in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 and cited in each affected ADR's `Known Deviations`. No confirmed deviation remains.

## Reading Order

| Category | File |
|---|---|
| ADR Index | `adr_01_index.md` |
| Workflow Engine Mandatory | `adr_02_02_001_agent-workflow-engine-mandatory.md` |
| Config Isolation | `adr_02_01_002_platform-config-isolation.md` |
| Tool Registry Authority | `adr_02_02_003_agent-runtime-tool-registry-routing-authority.md` |
| Environment Failure Handling | `adr_02_01_004_platform-environment-failure-handling-policy.md` |
| RAG Source-Derived Index | `adr_02_06_005_rag-source-derived-index-relationships.md` |
| EventBus Persistence & SSE | `adr_02_04_006_eventbus-sqlite-persistence-and-sse-delivery.md` |
| HTTP MCP Adoption | `adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` |
| SQLite 4DB Separation | `adr_02_05_008_db-sqlite-4db-separation.md` |
| RAG FTS5 Text Separation | `adr_02_06_009_rag-fts5-text-separation.md` |
| RAG Fallback | `adr_02_06_010_rag-fallback.md` |
| Git MCP Server-Side Write | `adr_02_03_012_mcp-git-server-side-write-enforcement.md` |
| EventBus Authentication | `adr_02_04_013_eventbus-authentication-authorization.md` |
| Agent Control Plane Boundaries | `adr_02_02_014_agent-control-plane-responsibility-boundaries.md` |
| Reference Document Class Disposition | `adr_02_07_015_docs-reference-document-class-disposition.md` |

## File Naming

Files in this directory follow `adr_NN_<name>.md`: `adr_00_` is this guide, `adr_01_` is the index, and each ADR is `adr_02_<GG>_<NNN>_<group>-<topic>.md`.

- `<GG>` is the two-digit group number; it orders ADRs of one theme next to each other in a directory listing.
- `<NNN>` is the three-digit ADR number and is the stable key. The ADR ID in text (for example `ADR-006`) is unchanged by grouping.
- `<group>-<topic>` is the group word followed by the topic slug; a leading theme word that duplicates the group word is not repeated.
- A new ADR chooses an existing group from the registry below, or adds a new group number and word to this registry in the same change. The group is recorded in the file name and in the `Group` column of the ADR List in `adr_01_index.md`.

| Group | Word | ADRs |
|---|---|---|
| 01 | platform | 002, 004 |
| 02 | agent | 001, 003, 014 |
| 03 | mcp | 007, 012 |
| 04 | eventbus | 006, 013 |
| 05 | db | 008 |
| 06 | rag | 005, 009, 010 |
| 07 | docs | 015 |

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
