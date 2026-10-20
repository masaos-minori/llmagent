---
title: "Chunk Japanese Mixin, Pipeline Utils, and FTS5 Notes"
area: rag
tags:
  - chunk-japanese
  - pipeline-utils
  - fts5
related:
  - rag_00_document-guide.md
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_02_02_ingestion_pipeline-crawler.md
  - rag_02_03_ingestion_pipeline-chunksplitter.md
  - rag_02_04_ingestion_pipeline-ingester.md
  - rag_02_07_ingestion_pipeline-utils.md
  - rag_02_09_ingestion_pipeline-shared-utilities.md
  - rag_03_06_query_pipeline-helpers-and-cache.md
  - rag_05_01-configuration-reference.md
  - adr_02_06_009_rag-fts5-text-separation.md
---


# RAG Ingestion Pipeline

- System Overview → [rag_01_system_overview.md](rag_01_system_overview.md)
- Configuration → [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md)

---

## 8. Chunk Japanese Mixin (`scripts/rag/ingestion/chunk_japanese.py`)

### 8.1 Module Overview

`chunk_japanese.py` — `ChunkJapaneseMixin`: Morphological analysis-based chunking for Japanese text using Sudachi SplitMode.C. Includes NFKC normalization, sentence boundary splitting, and buffer-based accumulation with overlap. Mixed into `ChunkSplitter` via multiple inheritance.

---

## 9. Pipeline Utils (`scripts/rag/ingestion/pipeline_utils.py`)

### 9.1 Module Overview

`pipeline_utils.py` — Shared I/O utilities for the RAG ingestion pipeline: reading chunk JSONs with validation, collecting source files, and checking processed sentinels. Provides the `ChunkJsonRaw` TypedDict for raw chunk/crawl JSON payload fields.

For exhaustive signature and constant detail, see `scripts/rag/ingestion/pipeline_utils.py`.

---

## 10. Shared Utilities Summary (`scripts/rag/utils.py`)

Stateless helpers shared by ingestion and query code (vectors, Unicode normalization, prompt-injection sanitization, URL validation). Details → [rag_02_09_ingestion_pipeline-shared-utilities.md](rag_02_09_ingestion_pipeline-shared-utilities.md)

---

## 11. Note on FTS5 Implementation

- FTS5 / LLM content separation (`chunks.content` vs `chunks.normalized_content`, the FTS5 triggers, and the invariants): see [ADR-009](../10_adr/adr_02_06_009_rag-fts5-text-separation.md).
- Japanese chunk normalization at ingestion: see [rag_02_03_ingestion_pipeline-chunksplitter.md](rag_02_03_ingestion_pipeline-chunksplitter.md).
- FTS5 query tokenization and the query token limit: see the Japanese FTS5 Tokenization part of [rag_03_06_query_pipeline-helpers-and-cache.md](rag_03_06_query_pipeline-helpers-and-cache.md).

---

## Keywords

- chunk-japanese
- pipeline-utils
- fts5
- rag
