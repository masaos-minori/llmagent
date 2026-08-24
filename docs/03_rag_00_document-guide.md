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
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
  - 03_rag_90_inconsistencies_and_known_issues.md
  - 03_rag_91_design_notes.md
---

# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to determine which chapter you should open.

---



## Reading Order

``` text
01 System Overview → 02 Ingestion Pipeline → 03 Query Pipeline → 04 Data Model → 05 Configuration → 90 Known Issues → 91 Design Notes
```

---

## AI Query Routing Table

| Question | File |
|---|---|
| What is the RAG system, and how does it work overall? | `03_rag_01` |
| What are the ingestion pipeline scripts, and how do I run them? | `03_rag_02`, `03_rag_05` |
| What do `WebCrawler` / `ChunkSplitter` / `RagIngester` do (API)? | `03_rag_02` |
| How does the query pipeline work (stages, RRF, reranking)? | `03_rag_03` |
| What is the `RagPipeline` API? | `03_rag_03` |
| How does `use_rrf` affect fusion mode? | `03_rag_03` |
| What is the SQLite schema for the RAG database? | `03_rag_04` |
| What are `RawHit`, `MergedHit`, and `RankedHit`? | `03_rag_04` |
| What are the configuration parameters? | `03_rag_05` |
| Are there any known bugs or behavioral inconsistencies? | `03_rag_90` |
| What are the established design invariants regarding FTS5/LLM content separation and table responsibilities? | `03_rag_91` |

---

## Canonical Source Rules

Only the restructured documents listed in the following file index are valid sources of specification.

| Domain | Canonical Source |
|---|---|
| System purpose, ingestion/query pipeline overview | `03_rag_01_system_overview.md` |
| File formats (JSON structure, field names) | `03_rag_02_01_ingestion_pipeline-overview.md`, `03_rag_04_01_dto-models_data.md` |
| Query pipeline behavior (stages, RRF, reranking, HTTP mode) | `03_rag_03_01_query_pipeline-overview.md` |
| Configuration parameters and operational commands | `03_rag_05_1-configuration-reference.md` |
| Known bugs, specification contradictions, unresolved issues | `03_rag_90_inconsistencies_and_known_issues.md` |
| Established design invariants and regression test gaps | `03_rag_91_design_notes.md`, `03_rag_91_design_notes.md` |

**Conflict Resolution**: If a contradiction is detected during review or implementation changes, modify the canonical file as defined by the Canonical Source Rule and add the detection date and details to `docs/03_rag_90_inconsistencies_and_known_issues.md`. If it cannot be resolved immediately, record it as an entry with a DOC-N label in the same file. For local checks, use `python tools/check_docs_consistency.py [target files...]`.

---

## File Index

| File | Description |
|---|---|
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | Entry point and routing guide |
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | System overview, architecture, prerequisites |
| [03_rag_02_01_ingestion_pipeline-overview.md](03_rag_02_01_ingestion_pipeline-overview.md) | Ingestion execution guide |
| [crawler-part1](03_rag_02_02_ingestion_pipeline-crawler.md) / [-part2](03_rag_02_02_ingestion_pipeline-crawler.md) | WebCrawler details |
| [chunksplitter-part1](03_rag_02_03_ingestion_pipeline-chunksplitter.md) / [-part2](03_rag_02_03_ingestion_pipeline-chunksplitter.md) | ChunkSplitter details |
| [ingester-part1](03_rag_02_04_ingestion_pipeline-ingester.md) / [-part2](03_rag_02_04_ingestion_pipeline-ingester.md) | RagIngester details |
| [03_rag_02_05_ingestion_pipeline-document-manager.md](03_rag_02_05_ingestion_pipeline-document-manager.md) | DocumentManager details |
| [03_rag_02_06_ingestion_pipeline-supporting-components.md](03_rag_02_06_ingestion_pipeline-supporting-components.md) | ETagManager + Config |
| [03_rag_02_07_ingestion_pipeline-utils.md](03_rag_02_07_ingestion_pipeline-utils.md) | Utility functions |
| [03_rag_02_08_ingestion_pipeline-shared.md](03_rag_02_08_ingestion_pipeline-shared.md) | Shared utilities |
| [03_rag_02_09_ingestion_pipeline-shared-utilities.md](03_rag_02_09_ingestion_pipeline-shared-utilities.md) | rag.utils details |
| [03_rag_03_01_query_pipeline-overview.md](03_rag_03_01_query_pipeline-overview.md) | Query pipeline overview |
| [rag-pipeline-class-part1](03_rag_03_02_query_pipeline-rag-pipeline-class.md) / [-part2](03_rag_03_02_query_pipeline-rag-pipeline-class.md) | RagPipeline class |
| [03_rag_03_03_query_pipeline-context-and-diagnostics.md](03_rag_03_03_query_pipeline-context-and-diagnostics.md) | Context + Diagnostics |
| [03_rag_03_04_query_pipeline-search-stages.md](03_rag_03_04_query_pipeline-search-stages.md) | Search stages |
| [03_rag_03_05_query_pipeline-augment-stages.md](03_rag_03_05_query_pipeline-augment-stages.md) | Augmentation stages |
| [helpers-and-cache-part1](03_rag_03_06_query_pipeline-helpers-and-cache.md) / [-part2](03_rag_03_06_query_pipeline-helpers-and-cache.md) | Helpers + Cache |
| [03_rag_03_07_query_pipeline-tests.md](03_rag_03_07_query_pipeline-tests.md) | Tests |
| [03_rag_04_01_dto-models_data.md](03_rag_04_01_dto-models_data.md) | DTO: models_data |
| [03_rag_04_02_dto-models_result.md](03_rag_04_02_dto-models_result.md) | DTO: models_result |
| [03_rag_04_03_dto-models_audit.md](03_rag_04_03_dto-models_audit.md) | DTO: models_audit |
| [03_rag_04_04_dto-models_config.md](03_rag_04_04_dto-models_config.md) | DTO: models_config |
| [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md) | DTO: types |
| [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md) | Configuration reference |
| [03_rag_05_2-execution-guide.md](03_rag_05_2-execution-guide.md) | Execution guide |
| [03_rag_05_3-logging.md](03_rag_05_3-logging.md) | Logging |
| [03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md) | Error handling |
| [03_rag_05_5-constraints-reference.md](03_rag_05_5-constraints-reference.md) | Constraints |
| [03_rag_05_6-local-file-re-ingestion.md](03_rag_05_6-local-file-re-ingestion.md) | Local file re-ingestion |
| [03_rag_05_7-rag-index-consistency-checks.md](03_rag_05_7-rag-index-consistency-checks.md) | Consistency checks |
| [03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md](03_rag_05_8-rag-mcp-internal-operations-direct-db-access.md) | MCP internal operations |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | Known issues |
| [03_rag_91_design_notes.md](03_rag_91_design_notes.md) | DESIGN-2 notes |
| [03_rag_91_design_notes.md](03_rag_91_design_notes.md) | DESIGN-3 notes |

---

## Governance

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Documentation Metadata](00_governance_02_documentation-metadata.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Related Documents

- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_90_inconsistencies_and_known_issues.md`
- `03_rag_91_design_notes.md`

## Related ADRs

- [ADR-005](adr/ADR-005-rag-source-derived-index-relationships.md) — RAGの正本と派生インデックスの関係
- [ADR-008](adr/ADR-008-sqlite-4db-separation.md) — SQLiteを4DBへ分離する
- [ADR-009](adr/ADR-009-rag-ft5-text-separation.md) — RAGのFTS5検索用テキストとLLM提示用テキスト分離
- [ADR-010](adr/ADR-010-rag-fallback.md) — RAGの外部実行失敗時のインプロセスフォールバック

## Keywords

rag
documentation
guide
routing
file-index
