# Implementation: docs/03_rag_02_ingestion_pipeline.md

## Goal

Create a detailed reference for all three ingestion scripts (WebCrawler, ChunkSplitter,
RagIngester) consolidated in one file, preserving all API details and execution commands.

## Scope

- Content from: `03_rag-ref-crawler.md` (all sections)
- Content from: `03_rag-ref-splitter.md` (all sections)
- Content from: `03_rag-ref-ingester.md` (all sections)
- Content from: `03_rag-ingestion-run.md` (execution commands, file lifecycle)
- Content from: `03_rag-ingestion-pipeline.md` (utils.py, FTS5 notes)
- Output: `docs/03_rag_02_ingestion_pipeline.md`
- Not covered: query pipeline stages, DB schema details (go to 04), config tables (go to 05)

## Assumptions

- canonical source for module names: `03_rag-ingestion-run.md` (crawler.py, ingester.py)
- ref-* files are canonical for API details
- Document naming inconsistency (web_crawler.py vs crawler.py) must be flagged with reference to 90

## Implementation

### Target file

`docs/03_rag_02_ingestion_pipeline.md`

### Procedure

1. Section 1: Execution Guide — copy CLI commands and file lifecycle from `03_rag-ingestion-run.md`
2. Section 2: WebCrawler — all subsections from `03_rag-ref-crawler.md`
3. Section 3: ChunkSplitter — all subsections from `03_rag-ref-splitter.md`
4. Section 4: RagIngester — all subsections from `03_rag-ref-ingester.md`
5. Section 5: Shared Utilities (rag/utils.py) — from `03_rag-ingestion-pipeline.md`
6. Section 6: FTS5 Implementation Notes — from `03_rag-ingestion-pipeline.md`

### Method

- Start each script section with: Overview → Public Methods → Behavior Details →
  CLI Args → I/O Interface → Error Handling → Logging → Config Items
- Inline note on module naming inconsistency: see 03_rag_90 for details
- BUG-1/2/3 (ingester `_read_chunk_json` bug) must be flagged in the RagIngester section
  with a note pointing to 03_rag_90_inconsistencies.md for full analysis

### Details

RagIngester BUG-1/2/3 flag (brief, full detail in 90):
> **Known Issue:** `_read_chunk_json()` drops `chunking_strategy`, `normalized_content`,
> and `chunk_index` fields. See [03_rag_90_inconsistencies_and_known_issues.md](03_rag_90_inconsistencies_and_known_issues.md) BUG-1/2/3.

## Validation plan

- File exists at `docs/03_rag_02_ingestion_pipeline.md`
- Contains all CLI arguments for all 3 scripts with defaults
- Contains all config parameters for all 3 scripts
- BUG note present in RagIngester section
- Module naming inconsistency flag present
