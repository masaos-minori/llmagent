# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to choose which chapter to open.

---

## Purpose of this Document Set

These 7 files describe the RAG (Retrieval-Augmented Generation) system that indexes web
pages and local files, and injects relevant context into each LLM agent turn.

They replace the original 7 source files as the primary reference.

---

## Reading Order (Human)

```
01 System Overview        — start here for the big picture
    ↓
02 Ingestion Pipeline     — crawl, chunk, embed, store
    ↓
03 Query Pipeline         — 6-stage retrieval and augmentation
    ↓
04 Data Model             — DB schema, type definitions, public interfaces
    ↓
05 Configuration          — config files, run commands, logging, error handling
    ↓
90 Inconsistencies        — known bugs, spec conflicts, open questions
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

---

## Canonical Source Rules

The restructured docs in the File Index below are the only active spec sources.

| Domain | Canonical source |
|---|---|
| System purpose, ingestion and query pipeline overviews | `03_rag_01_system_overview.md` |
| File formats (JSON structure, field names) | `03_rag_02_ingestion_pipeline.md`, `03_rag_04_data_model_and_interfaces.md` |
| Query pipeline behavior (stages, RRF, rerank, HTTP mode) | `03_rag_03_query_pipeline.md` |
| Configuration parameters and operations commands | `03_rag_05_configuration_and_operations.md` |
| Known bugs, spec conflicts, open questions | `03_rag_90_inconsistencies_and_known_issues.md` |

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
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | System purpose, ingestion and query pipeline overviews, prerequisites, constraints |
| [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md) | Execution guide; WebCrawler, ChunkSplitter, RagIngester APIs; FTS5 notes |
| [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) | RagPipeline API; 6-stage details; PipelineContext; SemanticCache; helper classes |
| [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md) | File formats; SQLite schema; hit type hierarchy; public interface summary |
| [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md) | Config parameter tables; run commands; logging; error handling reference |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | Design notes (DESIGN-2, DESIGN-3) and active issues tracking |

---
