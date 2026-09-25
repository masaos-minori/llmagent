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
  - rag_04_05_dto-types.md
  - rag_05_1-configuration-reference.md
  - governance_03_issue-and-uncertainty-management.md
  - rag_91_design_notes.md
---

# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to determine which chapter you should open.

---



## Reading Order

``` text
01 System Overview → 02 Ingestion Pipeline → 03 Query Pipeline → 04 Data Model → 05 Configuration → 91 Design Notes
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
| What is the SQLite schema for the RAG database? | `rag_04` |
| What are `RawHit`, `MergedHit`, and `RankedHit`? | `rag_04` |
| What are the configuration parameters? | `rag_05` |
| Are there any known bugs or behavioral inconsistencies? | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: RAG) |
| What are the established design invariants regarding FTS5/LLM content separation and table responsibilities? | `rag_91` |

---

## Canonical Source Rules

Only the restructured documents listed in the following file index are valid sources of specification.

| Domain | Canonical Source |
|---|---|
| System purpose, ingestion/query pipeline overview | `rag_01_system_overview.md` |
| File formats (JSON structure, field names) | `rag_02_01_ingestion_pipeline-overview.md`, `rag_04_01_dto-models_data.md` |
| Query pipeline behavior (stages, RRF, reranking, HTTP mode) | `rag_03_01_query_pipeline-overview.md` |
| Configuration parameters and operational commands | `rag_05_1-configuration-reference.md` |
| Known bugs, specification contradictions, unresolved issues | `governance_03_issue-and-uncertainty-management.md` (Part 1, Area: RAG) |
| Established design invariants and regression test gaps | `rag_91_design_notes.md`, `rag_91_design_notes.md` |

**Conflict Resolution**: If a contradiction is detected during review or implementation changes, modify the canonical file as defined by the Canonical Source Rule and add an entry to `docs/governance_03_issue-and-uncertainty-management.md` Part 1 (Area: RAG) with the detection date and details. For local checks, use `python tools/check_docs_consistency.py [target files...]`.

---

## File Index

| File | Description |
|---|---|
| [rag_00_document-guide.md](rag_00_document-guide.md) | Entry point and routing guide |
| [rag_01_system_overview.md](rag_01_system_overview.md) | System overview, architecture, prerequisites |
| [rag_02_01_ingestion_pipeline-overview.md](rag_02_01_ingestion_pipeline-overview.md) | Ingestion execution guide |
| [crawler-part1](rag_02_02_ingestion_pipeline-crawler.md) / [-part2](rag_02_02_ingestion_pipeline-crawler.md) | WebCrawler details |
| [chunksplitter-part1](rag_02_03_ingestion_pipeline-chunksplitter.md) / [-part2](rag_02_03_ingestion_pipeline-chunksplitter.md) | ChunkSplitter details |
| [ingester-part1](rag_02_04_ingestion_pipeline-ingester.md) / [-part2](rag_02_04_ingestion_pipeline-ingester.md) | RagIngester details |
| [rag_02_05_ingestion_pipeline-document-manager.md](rag_02_05_ingestion_pipeline-document-manager.md) | DocumentManager details |
| [rag_02_06_ingestion_pipeline-supporting-components.md](rag_02_06_ingestion_pipeline-supporting-components.md) | ETagManager + Config |
| [rag_02_07_ingestion_pipeline-utils.md](rag_02_07_ingestion_pipeline-utils.md) | Utility functions |
| [rag_02_08_ingestion_pipeline-shared.md](rag_02_08_ingestion_pipeline-shared.md) | Shared utilities |
| [rag_02_09_ingestion_pipeline-shared-utilities.md](rag_02_09_ingestion_pipeline-shared-utilities.md) | rag.utils details |
| [rag_03_01_query_pipeline-overview.md](rag_03_01_query_pipeline-overview.md) | Query pipeline overview |
| [rag-pipeline-class-part1](rag_03_02_query_pipeline-rag-pipeline-class.md) / [-part2](rag_03_02_query_pipeline-rag-pipeline-class.md) | RagPipeline class |
| [rag_03_03_query_pipeline-context-and-diagnostics.md](rag_03_03_query_pipeline-context-and-diagnostics.md) | Context + Diagnostics |
| [rag_03_04_query_pipeline-search-stages.md](rag_03_04_query_pipeline-search-stages.md) | Search stages |
| [rag_03_05_query_pipeline-augment-stages.md](rag_03_05_query_pipeline-augment-stages.md) | Augmentation stages |
| [helpers-and-cache-part1](rag_03_06_query_pipeline-helpers-and-cache.md) / [-part2](rag_03_06_query_pipeline-helpers-and-cache.md) | Helpers + Cache |
| [rag_03_07_query_pipeline-tests.md](rag_03_07_query_pipeline-tests.md) | Tests |
| [rag_04_01_dto-models_data.md](rag_04_01_dto-models_data.md) | DTO: models_data |
| [rag_04_02_dto-models_result.md](rag_04_02_dto-models_result.md) | DTO: models_result |
| [rag_04_03_dto-models_audit.md](rag_04_03_dto-models_audit.md) | DTO: models_audit |
| [rag_04_04_dto-models_config.md](rag_04_04_dto-models_config.md) | DTO: models_config |
| [rag_04_05_dto-types.md](rag_04_05_dto-types.md) | DTO: types |
| [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md) | Configuration reference |
| [rag_05_2-execution-guide.md](rag_05_2-execution-guide.md) | Execution guide |
| [rag_05_3-logging.md](rag_05_3-logging.md) | Logging |
| [rag_05_4-error-handling-reference.md](rag_05_4-error-handling-reference.md) | Error handling |
| [rag_05_5-constraints-reference.md](rag_05_5-constraints-reference.md) | Constraints |
| [rag_05_6-local-file-re-ingestion.md](rag_05_6-local-file-re-ingestion.md) | Local file re-ingestion |
| [rag_05_7-rag-index-consistency-checks.md](rag_05_7-rag-index-consistency-checks.md) | Consistency checks |
| [rag_05_8-rag-mcp-internal-operations-direct-db-access.md](rag_05_8-rag-mcp-internal-operations-direct-db-access.md) | MCP internal operations |
| [governance_03_issue-and-uncertainty-management.md](/home/sugimoto/llmagent/docs/00_governance/governance_03_issue-and-uncertainty-management.md) | Known issues (all areas) |
| [rag_91_design_notes.md](rag_91_design_notes.md) | DESIGN-2 notes |
| [rag_91_design_notes.md](rag_91_design_notes.md) | DESIGN-3 notes |

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](/home/sugimoto/llmagent/docs/00_governance/governance_01_documentation-policy.md)
- [Documentation Metadata](/home/sugimoto/llmagent/docs/00_governance/governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](/home/sugimoto/llmagent/docs/00_governance/governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](/home/sugimoto/llmagent/docs/00_governance/governance_04_documentation-checks.md)

## Related Documents

- `rag_01_system_overview.md`
- `rag_02_01_ingestion_pipeline-overview.md`
- `rag_03_01_query_pipeline-overview.md`
- `rag_04_05_dto-types.md`
- `rag_05_1-configuration-reference.md`
- `rag_91_design_notes.md`

## Related ADRs

- [ADR-005](/home/sugimoto/llmagent/docs/10_adr/ADR-005-rag-source-derived-index-relationships.md) — RAGの正本と派生インデックスの関係
- [ADR-008](/home/sugimoto/llmagent/docs/10_adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する
- [ADR-009](/home/sugimoto/llmagent/docs/10_adr/ADR-009-rag-ft5-text-separation.md) — RAGのFTS5検索用テキストとLLM提示用テキスト分離
- [ADR-010](/home/sugimoto/llmagent/docs/10_adr/ADR-010-rag-fallback.md) — RAGの外部実行失敗時のインプロセスフォールバック

## Keywords

rag
documentation
guide
routing
file-index
