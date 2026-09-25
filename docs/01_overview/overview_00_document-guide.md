---
title: "System Overview Index"
area: overview
tags:
  - system-overview
  - architecture
  - introduction
  - index
related:
  - overview-arch-01-process.md
  - overview-arch-02-pipelines.md
  - overview-arch-03-features.md
  - overview-files-01-build.md
  - overview-files-02-rag.md
  - overview-files-03-scripts.md
  - overview-files-04-shared.md
  - overview-files-05-config.md
  - overview-files-06-misc.md
  - 02_deployment.md
source:
  - 01_overview.md
---

# Overview, Architecture, and File Structure (Index)

| File | Content |
|---|---|
| [overview-arch-01-process.md](overview-arch-01-process.md) | Process Architecture (LLM service, MCP server, separation of configuration) |
| [overview-arch-02-pipelines.md](overview-arch-02-pipelines.md) | Pipeline Architecture (Ingestion/Search pipeline, turn processing order, workflow mode) |
| [overview-arch-03-features.md](overview-arch-03-features.md) | Feature Architecture (Implemented features, implementation notes) |
| [overview-files-01-build.md](overview-files-01-build.md) | Build and Model related file structure |
| [overview-files-02-rag.md](overview-files-02-rag.md) | RAG related file structure |
| [overview-files-03-scripts.md](overview-files-03-scripts.md) 〜 part5 | File structure under scripts directory (split into 5 parts) |
| [overview-files-04-shared.md](overview-files-04-shared.md) 〜 part2 | Shared infrastructure file structure (split into 2 parts) |
| [overview-files-05-config.md](overview-files-05-config.md) | Configuration file structure |
| [overview-files-06-misc.md](overview-files-06-misc.md) | Other file structures |
| [02_deployment.md](02_deployment.md) | Deployment Topology (assumes single host/multiple hosts), environment setup, and service startup |

## Implementation Intent

- Split into 3 files by H2 boundaries: process, pipelines, features → `[overview-arch-01-process.md](overview-arch-01-process.md)`, `[overview-arch-02-pipelines.md](overview-arch-02-pipelines.md)`, `[overview-arch-03-features.md](overview-arch-03-features.md)`
- Split into 6 files by logical directory boundaries: build, rag, scripts, shared, config, misc → `[overview-files-01-build.md](overview-files-01-build.md)`, `[overview-files-02-rag.md](overview-files-02-rag.md)`, `[overview-files-03-scripts.md](overview-files-03-scripts.md)`, `[overview-files-04-shared.md](overview-files-04-shared.md)`, `[overview-files-05-config.md](overview-files-05-config.md)`, `[overview-files-06-misc.md](overview-files-06-misc.md)`
- Added YAML Front Matter including title/category/tags/related documents/keywords to each file
- This file is the system-wide overview index. Refer to the following catalogs for each detailed document set

## Related Documents

- `overview-arch-01-process.md`
- `overview-arch-02-pipelines.md`
- `overview-arch-03-features.md`
- `overview-files-01-build.md`
- `overview-files-02-rag.md`
- `overview-files-03-scripts.md`
- `overview-files-04-shared.md`
- `overview-files-05-config.md`
- `overview-files-06-misc.md`
- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`02_deployment.md`~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted)~~ (deleted),`
