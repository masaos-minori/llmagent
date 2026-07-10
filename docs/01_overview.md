---
title: "System Overview Index"
category: overview
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
source:
  - 01_overview.md
---

# Overview & Architecture & File Structure (Index)

| File | Content |
|---|---|
| [01_overview-arch-01-process.md](01_overview-arch-01-process.md) | Process architecture (LLM services, MCP servers, configuration isolation) |
| [01_overview-arch-02-pipelines.md](01_overview-arch-02-pipelines.md) | Pipeline architecture (ingestion/query pipelines, turn processing order, workflow modes) |
| [01_overview-arch-03-features.md](01_overview-arch-03-features.md) | Feature architecture (implemented features, implementation notes) |
| [01_overview-files-01-build.md](01_overview-files-01-build.md) | Build and models file structure |
| [01_overview-files-02-rag.md](01_overview-files-02-rag.md) | RAG files file structure |
| [01_overview-files-03-scripts.md](01_overview-files-03-scripts.md) | Scripts file structure |
| [01_overview-files-04-shared.md](01_overview-files-04-shared.md) | Shared infrastructure file structure |
| [01_overview-files-05-config.md](01_overview-files-05-config.md) | Configuration file structure |
| [01_overview-files-06-misc.md](01_overview-files-06-misc.md) | Miscellaneous file structure |

## Implementation Intent

- Split `01_overview-arch.md` into 3 files at H2 boundaries: process, pipelines, features
- Split `01_overview-files.md` into 6 files at directory-based logical boundaries: build, rag, scripts, shared, config, misc
- Each file has YAML Front Matter with title, category, tags, related documents, and keywords
- This file is the system-wide overview index. For detailed document sets, see the catalog below.

## Other Document Sets

| File | Content |
|---|---|
| [02_deployment.md](02_deployment.md) | Installation steps, deployment |
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | RAG document set guide (all files listed) |
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | MCP document set guide (all files listed) |
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | Agent document set guide (all files listed) |
| [90_shared_00_document-guide.md](90_shared_00_document-guide.md) | shared/DB document set guide (all files listed) |

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
- `02_deployment.md`

## Keywords

system-overview
architecture
introduction
index
overview
deployment
rag
mcp
agent
shared
