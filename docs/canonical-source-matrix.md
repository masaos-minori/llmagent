---
title: "Canonical Source Matrix"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Canonical Source Matrix

## Purpose

This matrix defines which artifact is authoritative for each decision target, what auxiliary evidence supports it, and where discrepancies are registered. It prevents treating Code as the top canonical source for ALL decision targets.

## Canonical Source Matrix

| Decision Target | Canonical | Auxiliary Evidence | Discrepancy Registration Target |
|-----------------|-----------|--------------------|----------------------------------|
| Adopted Architecture Decision | `docs/adrs/ADR-{NNN}.md` | Code, Test, Operational Observation | Known Issues |
| Requirements, External Behavior | `docs/{area}/{area}_specification.md` | Acceptance Test | Known Issues |
| Current Runtime Behavior | Source code under `scripts/`, `implementations/` | Runtime Log, Test | Known Issues |
| Expected Behavior | `tests/` + `docs/{area}/{area}_specification.md` | ADR | Known Issues |
| Effective Value in Production | Deployed Configuration (`config/*.toml`) | Startup Diagnostics | Configuration Drift |
| DB Schema | Schema Generator or official DDL | Schema Test | Known Issues |
| API Contract | API Schema or official Contract | Integration Test | Known Issues |
| Operational Procedures | Operations / Runbook | Operational Validation | Known Issues |
| Deprecated Items | `docs/00_governance_03_issue-and-uncertainty-management.md` | Code Search | Deprecated Items |
| Unconfirmed Items | `docs/00_governance_03_issue-and-uncertainty-management.md` | Investigation Evidence | Needs Confirmation |

## Notes

- **Code is canonical for current behavior, NOT for adopted design.** When code contradicts an ADR, the ADR represents the intended architecture and the discrepancy must be registered as a Known Issue.
- **Software Dependency Graph and Documentation Reference Graph are separated.** Do not mix them in the same graph.
- **Each area's document-guide identifies the canonical source within that area.** This matrix provides cross-cutting guidance only.

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

canonical source
decision target
evidence
discrepancy
ADR
code vs documentation