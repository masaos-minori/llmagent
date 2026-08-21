---
title: "ADR Index"
category: governance
tags:
  - adr
  - governance
related:
  - 00_index.md
  - 00_governance_01_documentation-governance.md
source:
  - 00_governance_11_adr-index.md
---

# ADR Index

## Purpose

This document indexes all Architecture Decision Records (ADRs) in the project. Each ADR documents a significant architectural decision with context, rationale, alternatives considered, and consequences.

## ADR List

| ADR | Title | Status | Date | Location |
|-----|-------|--------|------|----------|
| ADR-001 | Workflow Engine必須化 | Proposed | 2026-08-20 | [adr/ADR-001-workflow-engine-mandatory.md](adr/ADR-001-workflow-engine-mandatory.md) |
| ADR-002 | プロセス単位の設定所有権とConfig Isolation | Accepted | 2026-08-20 | [adr/ADR-002-config-isolation.md](adr/ADR-002-config-isolation.md) |
| ADR-003 | RuntimeToolRegistryを唯一のルーティング権威とする | Accepted | 2026-08-21 | [adr/ADR-003-runtime-tool-registry-routing-authority.md](adr/ADR-003-runtime-tool-registry-routing-authority.md) |
| ADR-004 | Environment Profile別障害方針 — Fail-Fast/Fail-Open | Proposed | 2026-08-21 | [adr/ADR-004-environment-profile-fail-fast-fail-open.md](adr/ADR-004-environment-profile-fail-fast-fail-open.md) |
| ADR-005 | RAGの正本と派生インデックスの関係 | Accepted | 2026-08-21 | [adr/ADR-005-rag-source-derived-index-relationships.md](adr/ADR-005-rag-source-derived-index-relationships.md) |
| ADR-006 | EventBusのSQLite永続化とSSE配信方式 | Accepted | 2026-08-21 | [adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md](adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md) |
| ADR-007 | HTTP MCP採用とstdio非サポート | Accepted | 2026-08-21 | [adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md](adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md) |
| ADR-008 | SQLiteを4DBへ分離する | Accepted | 2026-08-21 | [adr/ADR-008-sqlite-4db-separation.md](adr/ADR-008-sqlite-4db-separation.md) |
| ADR-009 | RAGのFTS5検索用テキストとLLM提示用テキスト分離 | Accepted | 2026-08-21 | [adr/ADR-009-rag-ft5-text-separation.md](adr/ADR-009-rag-ft5-text-separation.md) |
| ADR-010 | RAGの外部実行失敗時のインプロセスフォールバック | Accepted | 2026-08-21 | [adr/ADR-010-rag-fallback.md](adr/ADR-010-rag-fallback.md) |
| ADR-011 | Database Corruption Recovery Safety Boundary | Proposed | 2026-08-21 | [adr/ADR-011-database-corruption-recovery-safety-boundary.md](adr/ADR-011-database-corruption-recovery-safety-boundary.md) |
| ADR-012 | Git MCP Server-Side Write Enforcement | Proposed | 2026-08-21 | [adr/ADR-012-git-mcp-server-side-write-enforcement.md](adr/ADR-012-git-mcp-server-side-write-enforcement.md) |
| ADR-013 | MCP Tool Availability Model | Proposed | 2026-08-21 | [adr/ADR-013-mcp-tool-availability-model.md](adr/ADR-013-mcp-tool-availability-model.md) |

## Detailed ADR Registry

### ADR-001: Workflow Engine必須化

- **Status**: Proposed
- **Decision Scope**: system
- **Owner**: agent-team
- **Last Updated**: 2026-08-20
- **Related Areas**: Agent
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-003, ADR-004

### ADR-002: プロセス単位の設定所有権とConfig Isolation

- **Status**: Accepted
- **Decision Scope**: system
- **Owner**: platform-team
- **Last Updated**: 2026-08-20
- **Related Areas**: Agent, MCP, RAG, EventBus
- **Supersedes**: —
- **Related ADRs**: ADR-001, ADR-003, ADR-004, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010

### ADR-003: RuntimeToolRegistryを唯一のルーティング権威とする

- **Status**: Accepted
- **Decision Scope**: system
- **Owner**: mcp-team
- **Last Updated**: 2026-08-21
- **Related Areas**: MCP
- **Supersedes**: —
- **Related ADRs**: ADR-001, ADR-002, ADR-004, ADR-007

### ADR-004: Environment Profile別障害方針 — Fail-Fast/Fail-Open

- **Status**: Proposed
- **Decision Scope**: system
- **Owner**: platform-team
- **Last Updated**: 2026-08-21
- **Related Areas**: Agent, MCP, RAG, EventBus, Deployment
- **Supersedes**: —
- **Related ADRs**: ADR-001, ADR-002, ADR-003, ADR-007, ADR-010

### ADR-005: RAGの正本と派生インデックスの関係

- **Status**: Accepted
- **Decision Scope**: rag
- **Owner**: rag-team
- **Last Updated**: 2026-08-21
- **Related Areas**: RAG
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-008, ADR-009, ADR-010

### ADR-006: EventBusのSQLite永続化とSSE配信方式

- **Status**: Accepted
- **Decision Scope**: eventbus
- **Owner**: eventbus-team
- **Last Updated**: 2026-08-21
- **Related Areas**: EventBus
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-008

### ADR-007: HTTP MCP採用とstdio非サポート

- **Status**: Accepted
- **Decision Scope**: mcp
- **Owner**: mcp-team
- **Last Updated**: 2026-08-21
- **Related Areas**: MCP
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-003, ADR-004

### ADR-008: SQLiteを4DBへ分離する

- **Status**: Accepted
- **Decision Scope**: system
- **Owner**: platform-team
- **Last Updated**: 2026-08-21
- **Related Areas**: Shared/DB, Agent, RAG, EventBus
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-005, ADR-006, ADR-009, ADR-010

### ADR-009: RAGのFTS5検索用テキストとLLM提示用テキスト分離

- **Status**: Accepted
- **Decision Scope**: rag
- **Owner**: rag-team
- **Last Updated**: 2026-08-21
- **Related Areas**: RAG
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-005, ADR-008

### ADR-010: RAGの外部実行失敗時のインプロセスフォールバック

- **Status**: Accepted
- **Decision Scope**: rag
- **Owner**: rag-team
- **Last Updated**: 2026-08-21
- **Related Areas**: RAG
- **Supersedes**: —
- **Related ADRs**: ADR-002, ADR-004, ADR-005, ADR-008

### ADR-011: Database Corruption Recovery Safety Boundary

- **Status**: Proposed
- **Decision Scope**: shared/db
- **Owner**: agent-team
- **Last Updated**: 2026-08-21
- **Related Areas**: Shared/DB
- **Supersedes**: —
- **Related ADRs**: —

### ADR-012: Git MCP Server-Side Write Enforcement

- **Status**: Proposed
- **Decision Scope**: mcp/git
- **Owner**: agent-team
- **Last Updated**: 2026-08-21
- **Related Areas**: MCP
- **Supersedes**: —
- **Related ADRs**: —

### ADR-013: MCP Tool Availability Model

- **Status**: Proposed
- **Decision Scope**: mcp, agent
- **Owner**: agent-team
- **Last Updated**: 2026-08-21
- **Related Areas**: MCP, Agent
- **Supersedes**: —
- **Related ADRs**: ADR-003 (both establish `RuntimeToolRegistry` as the sole routing/availability authority)

## ADR Dependency Graph

```text
ADR-001 → ADR-004 → ADR-008
ADR-002 → ADR-001, ADR-003, ADR-005, ADR-006, ADR-007, ADR-008, ADR-009, ADR-010
ADR-003 → ADR-004, ADR-007
ADR-005 → ADR-008, ADR-009, ADR-010
ADR-006 → ADR-008
ADR-007 → ADR-004
ADR-009 → ADR-005
ADR-010 → ADR-004
ADR-013 → ADR-003
```

## Creating New ADRs

When creating a new ADR:

1. Determine the next available number (increment from the highest existing ADR number)
2. Use the `adr-template.md` template as the starting point
3. Place the ADR in `docs/adr/` directory
4. Update this index after creation
5. Update any existing documents that reference the old inline ADR section

## ADR Naming Convention

- Format: `ADR-{N}-{short-title}.md`
- `{N}`: Sequential number (zero-padded to 3 digits)
- `{short-title}`: Lowercase, hyphen-separated description of the decision

## ADR Status Definitions

- `Proposed`: Under review, not yet adopted
- `Accepted`: Adopted and currently valid
- `Rejected`: Considered but not adopted
- `Deprecated`: No longer recommended but still present in some places
- `Superseded`: Replaced by a later ADR

## Maintenance Rules

- New ADRs must be created within one week of the decision being made
- ADRs cannot be deleted without documenting what replaced them
- "Proposed" ADRs must be reviewed quarterly
- Superseded ADRs must remain accessible for historical reference

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
