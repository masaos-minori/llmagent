---
title: "RAG Documentation Guide"
category: rag
tags:
  - rag
  - documentation
  - guide
  - routing
  - file-index
related:
  - 03_rag_01_system_overview.md
  - 03_rag_02_ingestion_pipeline-overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_04_data_model_and_interfaces.md
  - 03_rag_05_configuration_and_operations.md
  - 03_rag_90_inconsistencies_and_known_issues.md
  - 03_rag_91_design_notes-part1.md
  - 03_rag_91_design_notes-part2.md
---

# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to choose which chapter to open.

---

## Reading Order

```
01 System Overview → 02 Ingestion Pipeline → 03 Query Pipeline → 04 Data Model → 05 Configuration → 90 Issues → 91 Design Notes
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What is the RAG system and how does it work overall? | `03_rag_01` |
| What are the ingestion pipeline scripts and how do I run them? | `03_rag_02`, `03_rag_05` |
| What does `WebCrawler` / `ChunkSplitter` / `RagIngester` do (API)? | `03_rag_02` |
| How does the query pipeline work (stages, RRF, rerank)? | `03_rag_03` |
| What is the `RagPipeline` API? | `03_rag_03` |
| How does `use_rrf` affect fusion mode? | `03_rag_03` |
| What is the SQLite schema for the RAG database? | `03_rag_04` |
| What are `RawHit`, `MergedHit`, `RankedHit`? | `03_rag_04` |
| What are the configuration parameters? | `03_rag_05` |
| Are there known bugs or behavior inconsistencies? | `03_rag_90` |
| What are the confirmed design invariants for FTS5/LLM content separation or table responsibilities? | `03_rag_91` |

---

## Canonical Source Rules

The restructured docs in the File Index below are the only active spec sources.

| Domain | Canonical source |
|---|---|
| System purpose, ingestion and query pipeline overviews | `03_rag_01_system_overview.md` |
| File formats (JSON structure, field names) | `03_rag_02_ingestion_pipeline-overview.md`, `03_rag_04_dto-models_data.md` |
| Query pipeline behavior (stages, RRF, rerank, HTTP mode) | `03_rag_03_query_pipeline.md` |
| Configuration parameters and operations commands | `03_rag_05_1-configuration-reference.md` |
| Known bugs, spec conflicts, open questions | `03_rag_90_inconsistencies_and_known_issues.md` |
| Confirmed design invariants and regression test gaps | `03_rag_91_design_notes-part1.md`, `03_rag_91_design_notes-part2.md` |

**Conflict resolution**: If two docs disagree on a fact and the conflict cannot be resolved immediately, record it as an entry in `03_rag_90_inconsistencies_and_known_issues.md` with a DOC-N label, then fix the root cause in the owning document.

### Running checks locally

Run the RAG documentation consistency checker from the project root:

```bash
python scripts/checks/check_docs_consistency.py
```

To check specific files:

```bash
python scripts/checks/check_docs_consistency.py docs/03_rag_01_system_overview.md
```

The checker runs 10 checks: broken headings, malformed tables, unclosed inline code, JSON not wrapped in fenced code blocks, stale artifact references (`.txt` -> `.json`), non-canonical command names, resolved issues under active sections, stale issue ID routing, deleted RAG source file references, and Migration Notes in active sections. Historical markers (`legacy`, `historical`, `archive only`, `resolved`, `was:`, `removed`) exempt lines from stale-pattern failures.

---

## File Index

| File | Description |
|---|---|
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | Entry point and routing guide |
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | System overview, architecture, prerequisites |
| [03_rag_02_ingestion_pipeline-overview.md](03_rag_02_ingestion_pipeline-overview.md) | Ingestion execution guide |
| [03_rag_02_ingestion_pipeline-crawler.md](03_rag_02_ingestion_pipeline-crawler.md) | WebCrawler detail |
| [03_rag_02_ingestion_pipeline-chunksplitter.md](03_rag_02_ingestion_pipeline-chunksplitter.md) | ChunkSplitter detail |
| [03_rag_02_ingestion_pipeline-ingester.md](03_rag_02_ingestion_pipeline-ingester.md) | RagIngester detail |
| [03_rag_02_ingestion_pipeline-document-manager.md](03_rag_02_ingestion_pipeline-document-manager.md) | DocumentManager detail |
| [03_rag_02_ingestion_pipeline-supporting-components.md](03_rag_02_ingestion_pipeline-supporting-components.md) | ETagManager + Configuration |
| [03_rag_02_ingestion_pipeline-utils.md](03_rag_02_ingestion_pipeline-utils.md) | Utility functions |
| [03_rag_02_ingestion_pipeline-shared.md](03_rag_02_ingestion_pipeline-shared.md) | Shared utilities |
| [03_rag_02_ingestion_pipeline-shared-utilities.md](03_rag_02_ingestion_pipeline-shared-utilities.md) | rag.utils detail |
| [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) | Query pipeline overview |
| [03_rag_03_query_pipeline-rag-pipeline-class.md](03_rag_03_query_pipeline-rag-pipeline-class.md) | RagPipeline class |
| [03_rag_03_query_pipeline-context-and-diagnostics.md](03_rag_03_query_pipeline-context-and-diagnostics.md) | Context + diagnostics |
| [03_rag_03_query_pipeline-search-stages.md](03_rag_03_query_pipeline-search-stages.md) | Search stages |
| [03_rag_03_query_pipeline-augment-stages.md](03_rag_03_query_pipeline-augment-stages.md) | Augment stages |
| [03_rag_03_query_pipeline-helpers-and-cache.md](03_rag_03_query_pipeline-helpers-and-cache.md) | Helpers + cache |
| [03_rag_03_query_pipeline-tests.md](03_rag_03_query_pipeline-tests.md) | Tests |
| [03_rag_04_dto-models_data.md](03_rag_04_dto-models_data.md) | DTO: models_data |
| [03_rag_04_dto-models_result.md](03_rag_04_dto-models_result.md) | DTO: models_result |
| [03_rag_04_dto-models_audit.md](03_rag_04_dto-models_audit.md) | DTO: models_audit |
| [03_rag_04_dto-models_config.md](03_rag_04_dto-models_config.md) | DTO: models_config |
| [03_rag_04_dto-types.md](03_rag_04_dto-types.md) | DTO: types |
| [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md) | Config reference |
| [03_rag_05_2-execution-guide.md](03_rag_05_2-execution-guide.md) | Execution guide |
| [03_rag_05_3-logging.md](03_rag_05_3-logging.md) | Logging |
| [03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md) | Error handling |
| [03_rag_05_5-constraints-reference.md](03_rag_05_5-constraints-reference.md) | Constraints |
| [03_rag_05_6-local-file-re-ingestion.md](03_rag_05_6-local-file-re-ingestion.md) | Local re-ingestion |
| [03_rag_05_rag-index-consistency-checks.md](03_rag_05_rag-index-consistency-checks.md) | Consistency checks |
| [03_rag_05_rag-mcp-internal-operations-direct-db-access.md](03_rag_05_rag-mcp-internal-operations-direct-db-access.md) | MCP internal ops |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | Known issues |
| [03_rag_91_design_notes-part1.md](03_rag_91_design_notes-part1.md) | DESIGN-2 notes |
| [03_rag_91_design_notes-part2.md](03_rag_91_design_notes-part2.md) | DESIGN-3 notes |

---

## Related Documents

- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-overview.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_04_data_model_and_interfaces.md`
- `03_rag_05_configuration_and_operations.md`
- `03_rag_90_inconsistencies_and_known_issues.md`
- `03_rag_91_design_notes-part1.md`
- `03_rag_91_design_notes-part2.md`

## Keywords

rag
documentation
guide
routing
file-index
