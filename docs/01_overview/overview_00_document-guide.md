---
title: "System Overview Index"
area: overview
tags:
  - system-overview
  - architecture
  - introduction
  - index
related:
  - overview_01_01-arch-process.md
  - overview_01_02-arch-pipelines.md
  - overview_01_03-arch-features.md
  - overview_02_files.md
---

# Overview, Architecture, and File Structure (Index)

| File | Content |
|---|---|
| [overview_01_01-arch-process.md](overview_01_01-arch-process.md) | Process Architecture (LLM service, MCP server, separation of configuration) |
| [overview_01_02-arch-pipelines.md](overview_01_02-arch-pipelines.md) | Pipeline Architecture (Ingestion/Search pipeline, turn processing order, workflow mode) |
| [overview_01_03-arch-features.md](overview_01_03-arch-features.md) | Feature Architecture (Implemented features, implementation notes) |
| [overview_02_files.md](overview_02_files.md) | File structure (build/models, RAG, scripts, shared infrastructure, configuration, miscellaneous) |

## Implementation Intent

- Architecture is split by H2 boundaries: process, pipelines, features → `[overview_01_01-arch-process.md](overview_01_01-arch-process.md)`, `[overview_01_02-arch-pipelines.md](overview_01_02-arch-pipelines.md)`, `[overview_01_03-arch-features.md](overview_01_03-arch-features.md)`
- File structure is split by logical directory boundaries: build, rag, scripts, shared, config, misc → `[overview_02_files.md](overview_02_files.md)`
- This file is the system-wide overview index. Refer to the following catalogs for each detailed document set

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.

## Keywords

- system-overview
- architecture
- introduction
- index
