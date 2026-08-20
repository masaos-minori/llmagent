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
