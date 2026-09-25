---
title: "Overview: Document Guide"
area: overview
tags:
  - overview
  - document-guide
related:
  - ../00_index.md
  - 01_overview.md
---
# Overview: Document Guide

## Purpose

These documents describe the system-wide architecture, process layout, pipeline flows, feature inventory, and file structure. Use them as the starting point for understanding the entire project.

## Reading Order

| Category | File |
|---|---|
| System Overview Index | `01_overview.md` |
| Process Architecture | `01_overview-arch-01-process.md` |
| Pipeline Architecture | `01_overview-arch-02-pipelines.md` |
| Feature Architecture | `01_overview-arch-03-features.md` |
| Build Files | `01_overview-files-01-build.md` |
| RAG Files | `01_overview-files-02-rag.md` |
| Scripts | `01_overview-files-03-scripts.md` |
| Shared Files | `01_overview-files-04-shared.md` |
| Config Files | `01_overview-files-05-config.md` |
| Misc Files | `01_overview-files-06-misc.md` |
| Deployment | `../90_deployment/02_deployment.md` |

## AI Query Routing

| Question | Rule |
|---|---|
| System-wide architecture & process layout | `01_overview-arch-01` |
| Pipeline flows & turn processing | `01_overview-arch-02` |
| Implemented features & design notes | `01_overview-arch-03` |
| Project file structure | `01_overview-files-*` |
| Deployment & environment setup | `../90_deployment/02_deployment.md` |

## Canonical Source Rule

See [System Overview Index](01_overview.md) for the complete system-wide architecture overview.

## Known Issues / Deferred Items

Known limitations, specification gaps, and pending items are centrally managed in `00_governance_03_issue-and-uncertainty-management.md`. Do not duplicate them in individual chapters.

## Reference API

No reference APIs exist in this directory. All files are architectural overviews.

## Related ADRs

- [ADR-008](adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する
- [ADR-015](adr/ADR-015-reference-document-class-disposition.md) — Reference document class disposition

## Related Documents

- `01_overview.md`
- `01_overview-arch-01-process.md`
- `01_overview-arch-02-pipelines.md`
- `01_overview-arch-03-features.md`
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- `../90_deployment/02_deployment.md`
