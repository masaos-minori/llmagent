---
title: "System Overview Index"
category: overview
tags:
  - system-overview
  - architecture
  - introduction
  - index
related:
  - 01_overview-arch-process.md
  - 01_overview-arch-pipelines.md
  - 01_overview-arch-features.md
  - 01_overview-files-build.md
  - 01_overview-files-rag.md
  - 01_overview-files-scripts.md
  - 01_overview-files-shared.md
  - 01_overview-files-config.md
  - 01_overview-files-misc.md
source:
  - 01_overview.md
---

# Overview & Architecture & File Structure (Index)

| File | Content |
|---|---|
| [01_overview-arch-process.md](01_overview-arch-process.md) | Process architecture (LLM services, MCP servers, configuration isolation) |
| [01_overview-arch-pipelines.md](01_overview-arch-pipelines.md) | Pipeline architecture (ingestion/query pipelines, turn processing order, workflow modes) |
| [01_overview-arch-features.md](01_overview-arch-features.md) | Feature architecture (implemented features, implementation notes) |
| [01_overview-files-build.md](01_overview-files-build.md) | Build and models file structure |
| [01_overview-files-rag.md](01_overview-files-rag.md) | RAG files file structure |
| [01_overview-files-scripts.md](01_overview-files-scripts.md) | Scripts file structure |
| [01_overview-files-shared.md](01_overview-files-shared.md) | Shared infrastructure file structure |
| [01_overview-files-config.md](01_overview-files-config.md) | Configuration file structure |
| [01_overview-files-misc.md](01_overview-files-misc.md) | Miscellaneous file structure |

## Implementation Intent

- Split `01_overview-arch.md` into 3 files at H2 boundaries: process, pipelines, features
- Split `01_overview-files.md` into 6 files at directory-based logical boundaries: build, rag, scripts, shared, config, misc
- Each file has YAML Front Matter with title, category, tags, related documents, and keywords
- This file is the system-wide overview index. For detailed document sets, see the catalog below.

## Implementation References

| File | Content |
|---|---|
| [01_overview-arch-process.md](01_overview-arch-process.md) | System-wide architecture |
| [01_overview-arch-pipelines.md](01_overview-arch-pipelines.md) | System-wide architecture |
| [01_overview-arch-features.md](01_overview-arch-features.md) | System-wide architecture |
| [01_overview-files-build.md](01_overview-files-build.md) | File/module structure |
| [01_overview-files-rag.md](01_overview-files-rag.md) | File/module structure |
| [01_overview-files-scripts.md](01_overview-files-scripts.md) | File/module structure |
| [01_overview-files-shared.md](01_overview-files-shared.md) | File/module structure |
| [01_overview-files-config.md](01_overview-files-config.md) | File/module structure |
| [01_overview-files-misc.md](01_overview-files-misc.md) | File/module structure |
| [02_deployment.md](02_deployment.md) | Installation steps, deployment |
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | RAG document set guide |
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | RAG system overview |
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | RAG document set guide (all files listed) |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | RAG known issues & inconsistencies |
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | MCP document set guide (all files listed) |
| [04_mcp_90_inconsistencies_and_known_issues.md](04_mcp_90_inconsistencies_and_known_issues.md) | MCP known issues & inconsistencies |
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | Agent document set guide |
| [05_agent_01_system-overview.md](05_agent_01_system-overview.md) | Agent system overview |
| [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md) | Runtime architecture |
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | Agent document set guide (all files listed) |
| [05_agent_12_reference-api.md](05_agent_12_reference-api.md) | API reference |
| [90_shared_00_document-guide.md](90_shared_00_document-guide.md) | shared/DB document set guide |
| [90_shared_00_document-guide.md](90_shared_00_document-guide.md) | shared/DB document set guide (all files listed) |
| [90_shared_90_inconsistencies_and_known_issues.md](90_shared_90_inconsistencies_and_known_issues.md) | shared/DB known issues & inconsistencies |

## Related Documents

- `01_overview-arch-process.md`
- `01_overview-arch-pipelines.md`
- `01_overview-arch-features.md`
- `01_overview-files-build.md`
- `01_overview-files-rag.md`
- `01_overview-files-scripts.md`
- `01_overview-files-shared.md`
- `01_overview-files-config.md`
- `01_overview-files-misc.md`
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
