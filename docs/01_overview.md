---
title: "System Overview Index"
area: overview
tags:
  - system-overview
  - architecture
  - introduction
  - index
related:
  - 01_overview-arch-01-process.md
  - 01_overview-arch-02-pipelines.md
  - 01_overview-arch-03-features.md
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts.md
  - 01_overview-files-04-shared.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
  - 02_deployment.md
source:
  - 01_overview.md
---

# Overview, Architecture, and File Structure (Index)

| File | Content |
|---|---|
| [01_overview-arch-01-process.md](01_overview-arch-01-process.md) | Process Architecture (LLM service, MCP server, separation of configuration) |
| [01_overview-arch-02-pipelines.md](01_overview-arch-02-pipelines.md) | Pipeline Architecture (Ingestion/Search pipeline, turn processing order, workflow mode) |
| [01_overview-arch-03-features.md](01_overview-arch-03-features.md) | Feature Architecture (Implemented features, implementation notes) |
| [01_overview-files-01-build.md](01_overview-files-01-build.md) | Build and Model related file structure |
| [01_overview-files-02-rag.md](01_overview-files-02-rag.md) | RAG related file structure |
| [01_overview-files-03-scripts.md](01_overview-files-03-scripts.md) 〜 part5 | File structure under scripts directory (split into 5 parts) |
| [01_overview-files-04-shared.md](01_overview-files-04-shared.md) 〜 part2 | Shared infrastructure file structure (split into 2 parts) |
| [01_overview-files-05-config.md](01_overview-files-05-config.md) | Configuration file structure |
| [01_overview-files-06-misc.md](01_overview-files-06-misc.md) | Other file structures |
| [02_deployment.md](02_deployment.md) | Deployment Topology (assumes single host/multiple hosts), environment setup, and service startup |

## Implementation Intent

- Split `01_overview-arch.md` into 3 files by H2 boundaries: process, pipelines, features
- Split `01_overview-files.md` into 6 files by logical directory boundaries: build, rag, scripts, shared, config, misc
- Added YAML Front Matter including title/category/tags/related documents/keywords to each file
- This file is the system-wide overview index. Refer to the following catalogs for each detailed document set

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-02-pipelines.md`
- `01_overview-arch-03-features.md`
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- `02_deployment.md`,`
