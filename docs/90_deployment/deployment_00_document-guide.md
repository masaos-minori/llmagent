---
title: "Deployment: Document Guide"
area: deployment
tags:
  - deployment
  - document-guide
related:
  - ../00_index.md
  - overview_00_document-guide.md
---
# Deployment: Document Guide

## Purpose

These documents describe the deployment process, environment setup, and operational procedures for this project. Use them when setting up or maintaining the production environment.

## Reading Order

| Category | File |
|---|---|
| Deployment Guide | `deployment_01_deployment.md` |

## AI Query Routing

| Question | Rule |
|---|---|
| Environment setup & provisioning | `deployment_01_deployment.md` §1 |
| DB initialization | `deployment_01_deployment.md` §3 |
| Service configuration | `deployment_01_deployment.md` §2 |
| Monitoring & health checks | `deployment_01_deployment.md` §2.4 |

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `governance_03_issue-and-uncertainty-management.md`. Do not duplicate them in individual chapters.

## Reference API

No reference APIs exist in this directory. All files are deployment guides.

## Related ADRs

- [ADR-008](../10_adr/ADR-008-sqlite-4db-separation.md) — Separating SQLite into Four Databases
- [ADR-015](../10_adr/ADR-015-reference-document-class-disposition.md) — Reference document class disposition

## Related Documents

- `../00_index.md`
- `../01_overview/overview_00_document-guide.md`

## Keywords

- deployment
- document-guide
