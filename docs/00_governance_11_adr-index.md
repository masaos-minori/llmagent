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
| ADR-002 | Database Corruption Recovery Safety Boundary | Proposed | 2026-08-21 | [adr/ADR-002-database-corruption-recovery-safety-boundary.md](adr/ADR-002-database-corruption-recovery-safety-boundary.md) |
| ADR-003 | Git MCP Server-Side Write Enforcement | Proposed | 2026-08-21 | [adr/ADR-003-git-mcp-server-side-write-enforcement.md](adr/ADR-003-git-mcp-server-side-write-enforcement.md) |
| ADR-004 | MCP Tool Availability Model | Proposed | 2026-08-21 | [adr/ADR-004-mcp-tool-availability-model.md](adr/ADR-004-mcp-tool-availability-model.md) |

**Numbering note:** ADR-001's own body lists aspirational future ADR numbers ("ADR-002: ワークフロー定義ファイルのスキーマ設計", "ADR-003: ワークフロー監視・メトリクス設計") that were never registered in this index. Per the numbering rule below (next available number, incremented from the highest *registered* ADR), ADR-002 through ADR-004 above were assigned to the decisions in this update instead. If the workflow-schema and workflow-monitoring ADRs are written later, they MUST take the next available numbers (ADR-005+), and ADR-001's body should be corrected to drop the stale forward references.

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
