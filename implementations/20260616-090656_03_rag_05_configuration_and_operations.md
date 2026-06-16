# Implementation: docs/03_rag_05_configuration_and_operations.md

## Goal

Consolidate all configuration parameters and operational procedures (execution guide,
troubleshooting, log file locations) into one file.

## Scope

- Content from: `03_rag-ref-crawler.md` section 2.7 (config params)
- Content from: `03_rag-ref-splitter.md` section 3.7 (config params)
- Content from: `03_rag-ref-ingester.md` section 4.7 (config params)
- Content from: `05_ref-rag.md` section 1.4 (RagConfig protocol, TOML values)
- Content from: `03_rag-ingestion-run.md` section 1 (execution guide)
- Content from: `03_spec_rag.md` sections 4, 5 (prerequisites, constraints)
- Output: `docs/03_rag_05_configuration_and_operations.md`
- Not covered: API signatures (03, 04), known bugs (90)

## Assumptions

- Config files: config/common.toml, config/rag_pipeline.toml, config/agent.toml
- Log files: /opt/llm/logs/crawl.log, /opt/llm/logs/chunk.log, /opt/llm/logs/ingest.log

## Implementation

### Target file

`docs/03_rag_05_configuration_and_operations.md`

### Procedure

1. Section 1: Configuration Reference
   - 1.1 config/rag_pipeline.toml — all params from crawler, splitter, ingester sections
   - 1.2 config/common.toml — embed_url, rag_db_path, sqlite_vec_so
   - 1.3 config/agent.toml — RagConfig-related params (llm_url, mqe_n_queries, rrf_k, etc.)
2. Section 2: Execution Guide
   - Prerequisites check commands
   - Step 1: crawl
   - Step 2: chunk split
   - Step 3: ingest
   - --force flag behavior per script
3. Section 3: Logging
   - Log file paths per script
   - Log level meanings per script
4. Section 4: Error Handling Reference
   - Error scenarios per component (crawler, splitter, ingester, pipeline)
5. Section 5: Constraints Reference
   - From 03_spec_rag.md section 5 (language detection, chunk sizes, crawl limits)

### Method

- Config tables: parameter | config file | default | description
- Use same table format across all 3 script config sections for consistency
- Execution guide: verbatim CLI commands from `03_rag-ingestion-run.md`

## Validation plan

- File exists at `docs/03_rag_05_configuration_and_operations.md`
- Config table covers: rag_src_dir, crawl_delay, max_depth, fetch_retry, fetch_timeout,
  crawl_concurrency, max_pages, min_chunk, max_chunk, chunk_overlap, md_index_enable,
  md_snippet_max_chars, embed_retry, embed_workers, embed_url, rag_db_path, sqlite_vec_so
- Execution commands present and verbatim
- Log file paths present for all 3 scripts
