# RAG Documentation Guide

This is the entry point for the restructured RAG system documentation.
Read this file first to choose which chapter to open.

---

## Purpose of this Document Set

These 7 files describe the RAG (Retrieval-Augmented Generation) system that indexes web
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
| What is the SQLite schema for the RAG database? | `03_rag_04` |
| What are `RawHit`, `MergedHit`, `RankedHit`? | `03_rag_04` |
| What are the configuration parameters? | `03_rag_05` |
| Are there known bugs or behavior inconsistencies? | `03_rag_90` |
| What is the `use_rrf` flag behavior? | `03_rag_90` (SPEC-1) |
| Why does `chunk_index` appear to always be 0? | `03_rag_90` (BUG-3, resolved) |

---

## Canonical Source Rules

Legacy source files (`03_spec_rag.md`, `03_rag-ref-*.md`, `03_rag-ingestion-*.md`, `05_ref-rag.md`) are deleted. The restructured docs in the File Index below are the only active spec sources.

| Domain | Canonical source |
|---|---|
| File formats (JSON structure, field names) | `03_rag_02_ingestion_pipeline.md`, `03_rag_04_data_model_and_interfaces.md` |
| Query pipeline behavior (stages, RRF, rerank, HTTP mode) | `03_rag_03_query_pipeline.md` |
| Configuration parameters and operations commands | `03_rag_05_configuration_and_operations.md` |
| Known bugs, spec conflicts, open questions | `03_rag_90_inconsistencies_and_known_issues.md` |

**Conflict resolution**: If two docs disagree on a fact and the conflict cannot be resolved immediately, record it as an entry in `03_rag_90_inconsistencies_and_known_issues.md` with a DOC-N label, then fix the root cause in the owning document.

---

## File Index

| File | Description |
|---|---|
| [03_rag_01_system_overview.md](03_rag_01_system_overview.md) | System purpose, ingestion and query pipeline overviews, prerequisites, constraints |
| [03_rag_02_ingestion_pipeline.md](03_rag_02_ingestion_pipeline.md) | Execution guide; WebCrawler, ChunkSplitter, RagIngester APIs; FTS5 notes |
| [03_rag_03_query_pipeline.md](03_rag_03_query_pipeline.md) | RagPipeline API; 6-stage details; PipelineContext; SemanticCache; helper classes |
| [03_rag_04_data_model_and_interfaces.md](03_rag_04_data_model_and_interfaces.md) | File formats; SQLite schema; hit type hierarchy; public interface summary |
| [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md) | Config parameter tables; run commands; logging; error handling reference |
| [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) | BUG-1/2/3 (resolved); SPEC-1/2; DOC-1/2; open questions OQ-1–7 |

---

## Legacy RAG Source Docs — Archive Policy (2026-06-26)

Archived docs are not part of current spec discovery — use the canonical docs listed in the File Index above.

Policy: **Delete**. Git history enables recovery.

Deleted documents:
- `docs/03_spec_rag.md`
- `docs/03_rag-ref-*.md`
- `docs/03_rag-ingestion-*.md`
- `docs/05_ref-rag.md`

If recovery is needed: `git show HEAD~N:docs/path/to/file.md`

---

## Migration Notes

### rag.llm re-export (removed 2026-06-26)

```python
# Before:
from rag.llm import RagLLM, get_embedding          # compat re-export (removed)
from rag.llm import RagExpansionError               # compat re-export (removed)

# After:
from rag.llm_client import RagLLM, get_embedding   # canonical
from rag.llm_prompts import RagExpansionError       # canonical
```

### PipelineStageResult (removed 2026-06-26)

```python
# Before:
from rag.types import PipelineStageResult  # removed

# After:
from rag.stage import StageResult          # canonical
```
