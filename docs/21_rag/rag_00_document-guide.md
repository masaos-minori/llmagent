---
title: "RAG Documentation Guide"
area: rag
tags:
  - rag
  - documentation
  - guide
  - routing
  - file-index
related:
  - rag_01_system_overview.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_03_01_query_pipeline-overview.md
  - rag_04_dto-models-types.md
  - rag_05_01-configuration-reference.md
  - governance_01_documentation-policy.md
  - governance_02_documentation-metadata.md
  - governance_03_issue-and-uncertainty-management.md
  - governance_04_documentation-checks.md
  - ADR-005-rag-source-derived-index-relationships.md
  - ADR-008-sqlite-4db-separation.md
  - ADR-009-rag-fts5-text-separation.md
  - ADR-010-rag-fallback.md
---

# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to determine which chapter you should open.

---



## Reading Order

``` text
01 System Overview → 02 Ingestion Pipeline → 03 Query Pipeline → 04 DTO Models → 05 Configuration and Operations
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What is the RAG system, and how does it work overall? | `rag_01` |
| What are the ingestion pipeline scripts, and how do I run them? | `rag_02`, `rag_05` |
| What do `WebCrawler` / `ChunkSplitter` / `RagIngester` do (API)? | `rag_02` |
| How does the query pipeline work (stages, RRF, reranking)? | `rag_03` |
| What is the `RagPipeline` API? | `rag_03` |
| How does `use_rrf` affect fusion mode? | `rag_03` |
| What is the SQLite schema for the RAG database (`rag.sqlite`)? | [db_02_architecture_and_schema-schema-reference.md](../41_db/db_02_architecture_and_schema-schema-reference.md) |
| What are `RawHit`, `MergedHit`, and `RankedHit`? | `rag_04` |
| What are the configuration parameters? | `rag_05` |
| Are there any known bugs or behavioral inconsistencies? | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: RAG) |
| What are the established design invariants regarding FTS5/LLM content separation and table responsibilities? | [ADR-009](../10_adr/ADR-009-rag-fts5-text-separation.md) / [ADR-005](../10_adr/ADR-005-rag-source-derived-index-relationships.md) |

---

## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.

---

## File Index

| File | Description |
|---|---|
| `rag_00_document-guide.md` | Entry point and routing guide |
| [rag_01_system_overview.md](rag_01_system_overview.md) | System overview, architecture, prerequisites |
| [rag_02_01_ingestion_pipeline-overview.md](rag_02_01_ingestion_pipeline-overview.md) | Ingestion execution guide |
| [rag_02_02_ingestion_pipeline-crawler.md](rag_02_02_ingestion_pipeline-crawler.md) | WebCrawler details |
| [rag_02_03_ingestion_pipeline-chunksplitter.md](rag_02_03_ingestion_pipeline-chunksplitter.md) | ChunkSplitter details |
| [rag_02_04_ingestion_pipeline-ingester.md](rag_02_04_ingestion_pipeline-ingester.md) | RagIngester details |
| [rag_02_05_ingestion_pipeline-document-manager.md](rag_02_05_ingestion_pipeline-document-manager.md) | DocumentManager details |
| [rag_02_06_ingestion_pipeline-supporting-components.md](rag_02_06_ingestion_pipeline-supporting-components.md) | ETagManager + Config |
| [rag_02_07_ingestion_pipeline-utils.md](rag_02_07_ingestion_pipeline-utils.md) | Utility functions |
| [rag_02_08_ingestion_pipeline-shared.md](rag_02_08_ingestion_pipeline-shared.md) | Shared utilities |
| [rag_02_09_ingestion_pipeline-shared-utilities.md](rag_02_09_ingestion_pipeline-shared-utilities.md) | rag.utils details |
| [rag_03_01_query_pipeline-overview.md](rag_03_01_query_pipeline-overview.md) | Query pipeline overview |
| [rag_03_02_query_pipeline-rag-pipeline-class.md](rag_03_02_query_pipeline-rag-pipeline-class.md) | RagPipeline class |
| [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md) | Context + Diagnostics |
| [rag_03_04_query_pipeline-search-stages.md](rag_03_04_query_pipeline-search-stages.md) | Search stages |
| [rag_03_05_query_pipeline-augment-stages.md](rag_03_05_query_pipeline-augment-stages.md) | Augmentation stages |
| [rag_03_06_query_pipeline-helpers-and-cache.md](rag_03_06_query_pipeline-helpers-and-cache.md) | Helpers + Retrieval Freshness |
| [rag_03_07_query_pipeline-tests.md](rag_03_07_query_pipeline-tests.md) | Tests |
| [rag_04_dto-models-types.md](rag_04_dto-models-types.md) | DTO: models_data, models_result, models_config, types |
| [rag_05_01-configuration-reference.md](rag_05_01-configuration-reference.md) | Configuration reference |
| [rag_05_02-execution-guide.md](rag_05_02-execution-guide.md) | Execution guide |
| [rag_05_03-logging.md](rag_05_03-logging.md) | Logging |
| [rag_05_04-error-handling-reference.md](rag_05_04-error-handling-reference.md) | Error handling |
| [rag_05_05-constraints-reference.md](rag_05_05-constraints-reference.md) | Constraints |
| [rag_05_06-local-file-re-ingestion.md](rag_05_06-local-file-re-ingestion.md) | Local file re-ingestion |
| [rag_05_07-rag-index-consistency-checks.md](rag_05_07-rag-index-consistency-checks.md) | Consistency checks |
| [rag_05_08-rag-mcp-internal-operations-direct-db-access.md](rag_05_08-rag-mcp-internal-operations-direct-db-access.md) | MCP internal operations |
| [governance_03_issue-and-uncertainty-management.md](../00_governance/governance_03_issue-and-uncertainty-management.md) | Known issues (all areas) |

---

## Keywords

- rag
- documentation
- guide
- routing
- file-index
