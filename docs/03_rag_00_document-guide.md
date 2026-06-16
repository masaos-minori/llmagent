# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to choose which chapter to open.

---

## Purpose of this Document Set

These 8 files describe the RAG (Retrieval-Augmented Generation) system that indexes web
pages and local files, and injects relevant context into each LLM agent turn.

They replace the original 7 source files (`03_spec_rag.md`, `03_rag-ref-*.md`,
`03_rag-ingestion-*.md`, `05_ref-rag.md`) as the primary reference.
The source files are retained as-is for historical reference.

---

## Reading Order (Human)

```
01 System Overview        — start here for the big picture
    ↓
02 Ingestion Pipeline     — crawl, chunk, embed, store
    ↓
03 Query Pipeline         — 5-stage retrieval and augmentation
    ↓
04 Data Model             — DB schema, type definitions, public interfaces
    ↓
05 Configuration          — config files, run commands, logging, error handling
    ↓
90 Inconsistencies        — known bugs, spec conflicts, open questions
    ↓
99 Source Mapping         — audit table (for restructuring verification only)
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
| What is the SQLite schema for the RAG database? | `03_rag_04` |
| What are `RawHit`, `MergedHit`, `RankedHit`? | `03_rag_04` |
| What are the configuration parameters? | `03_rag_05` |
| Are there known bugs or behavior inconsistencies? | `03_rag_90` |
| What is the `use_rrf` flag behavior? | `03_rag_90` (SPEC-1) |
| Why does `chunk_index` appear to always be 0? | `03_rag_90` (BUG-3) |
| Where did content from the old `03_spec_rag.md` section X go? | `03_rag_99` |

---

## Canonical Source Rules

- `ref-*` files are canonical for API details. Content now lives in `03_rag_02`–`03_rag_04`.
- `03_spec_rag.md` is canonical for constraints, DB schema, and known issues.
- `05_ref-rag.md` is canonical for query pipeline API. Content now lives in `03_rag_03`–`03_rag_04`.
- When old files and new files disagree, trust the new restructured files.

---

## File Index

| File | Description |
|---|---|
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | System purpose, ingestion and query pipeline overviews, prerequisites, constraints |
| [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md) | Execution guide; WebCrawler, ChunkSplitter, RagIngester APIs; FTS5 notes |
| [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) | RagPipeline API; 5-stage details; PipelineContext; SemanticCache; helper classes |
| [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md) | File formats; SQLite schema; hit type hierarchy; public interface summary |
| [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md) | Config parameter tables; run commands; logging; error handling reference |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | BUG-1/2/3; SPEC-1/2; DOC-1/2; open questions OQ-1–7 |
| [03_rag_99_source_mapping.md](03_rag_99_source_mapping.md) | Audit: maps every source section to its new location; coverage summary |

---

## Known Limitations

- `routing.md` has not yet been updated to reference these new files. Until updated,
  task routing will point to the old source files.
- The original source files (`03_spec_rag.md`, `03_rag-ref-*.md`, etc.) are retained
  unchanged. This document set supersedes them as the primary reference.
