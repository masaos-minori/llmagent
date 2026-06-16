# Implementation: docs/03_rag_04_data_model_and_interfaces.md

## Goal

Create a complete reference for the RAG data model: DB schema, hit type hierarchy,
public interfaces, and type definitions in one file.

## Scope

- Content from: `03_spec_rag.md` sections 9, 10
- Content from: `05_ref-rag.md` section 1.3 (exported types)
- Content from: `03_rag-ref-splitter.md` section 3.4 (chunk JSON format)
- Content from: `03_rag-ref-crawler.md` section 2.4 (crawler JSON format)
- Output: `docs/03_rag_04_data_model_and_interfaces.md`
- Not covered: pipeline behavior (03), config values (05), bugs (90)

## Assumptions

- 03_spec_rag.md section 9 is canonical for DB schema
- 05_ref-rag.md section 1.3 is canonical for hit types
- `chunking_strategy` column was added via `migrate_schema()` — document this

## Implementation

### Target file

`docs/03_rag_04_data_model_and_interfaces.md`

### Procedure

1. Section 1: File Format Specifications
   - Crawler output JSON (from 03_rag-ref-crawler.md §2.4)
   - Chunk file JSON (from 03_rag-ref-splitter.md §3.4)
2. Section 2: SQLite Schema (rag.sqlite)
   - documents table (with chunking_strategy migration note)
   - chunks table
   - chunks_fts (FTS5 virtual table, trigger behavior)
   - chunks_vec (sqlite-vec, BLOB format)
3. Section 3: Hit Type Hierarchy
   - RawHit, MergedHit, RankedHit, RagHit Union alias
   - Field availability by stage
4. Section 4: Public Interfaces
   - RagPipeline (brief signatures, link to 03 for full API)
   - WebCrawler, ChunkSplitter, RagIngester (brief signatures, link to 02)
   - PipelineStage Protocol
5. Section 5: Supporting Types
   - PipelineContext (brief, link to 03)
   - LLMMessage TypedDict
   - PipelineStageResult
   - RagConfig Protocol (fields list)

### Method

- DB schema: use column tables with type, constraints, and description
- Hit types: use table showing stage → available fields
- Interfaces: brief signatures with cross-references; do NOT repeat full API docs

## Validation plan

- File exists at `docs/03_rag_04_data_model_and_interfaces.md`
- All 4 DB tables documented with all columns
- chunking_strategy migration note present
- RawHit/MergedHit/RankedHit field table present
- RagConfig Protocol fields listed
