---
title: "Ingestion Pipeline Overview and Execution"
area: rag
tags:
  - ingestion-pipeline
  - execution-guide
  - crawler
  - chunk-splitter
  - ingester
  - rag
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_05_01-configuration-reference.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)

---

## 1. Execution Guide

The ingestion pipeline runs as three separate scripts (crawl, chunk split, embed and store) that hand off through files. For the commands, prerequisites, and `--force` semantics, see [rag_05_02-execution-guide.md](rag_05_02-execution-guide.md); for the current argument list, run each script with `--help`.

### File Lifecycle

| Path | Created By | Content | Deletion Policy |
|---|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks | Not deleted by the pipeline code; no automated retention or cleanup |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | chunk_splitter.py | Chunk information, Strategy | Moved out of `chunk/` after ingestion: to `registered/` on success, to `retry/` (embedding failures) or `failed/` (other failures, with a `.error.json` file) on failure |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | Chunk → Registered | No automated retention or cleanup; files accumulate until removed manually |

> **Retention:** No retention or cleanup setting exists for `rag-src/registered/`. See "Retention of `registered/`" in [rag_01_system_overview.md](rag_01_system_overview.md).
>
> **Artifact format:** Crawl and chunk artifacts are JSON written and read with `orjson`. The required keys and their Required/Nullable/Conditional classification are owned by the canonical field-contract table in [rag_02_03_ingestion_pipeline-chunksplitter.md](rag_02_03_ingestion_pipeline-chunksplitter.md).

`rag_src_dir` is set in the ingestion config files (see [Configuration Reference](rag_05_01-configuration-reference.md)).


## Keywords

- ingestion-pipeline
- execution-guide
- crawler
- chunk-splitter
- ingester
- rag
