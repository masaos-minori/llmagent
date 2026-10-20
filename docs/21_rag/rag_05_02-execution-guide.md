---
title: "Execution Guide"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_01-configuration-reference.md
  - rag_02_01_ingestion_pipeline-overview.md
---


# Execution Guide

## Prerequisites

```bash
# Ensure embed-llm is running
curl -s http://127.0.0.1:<PORT>/health

# Verify configuration files exist (defines rag_src_dir)
ls -la config/crawler.toml config/chunk_splitter.toml config/ingester.toml
```

## Step 1: Crawling

```bash
# Crawl all URLs specified in crawler.toml
uv run python scripts/rag/ingestion/crawler.py

# Crawl a single URL
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/" --lang en
```

## Step 2: Chunk Splitting

```bash
# Batch split unprocessed files
uv run python scripts/rag/ingestion/chunk_splitter.py

# Regenerate existing chunks
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

## Step 3: Embedding and Storage

```bash
# Embed and save to DB
uv run python scripts/rag/ingestion/ingester.py

# Force re-registration
uv run python scripts/rag/ingestion/ingester.py --force
```

### `--force` Behavior

- `crawler.py`: Not applicable (idempotent).
- `chunk_splitter.py`: Deletes existing chunks and regenerates them.
- `ingester.py`: Deletes `chunks_vec` rows and then the `documents` row (rows in `chunks` are removed by `ON DELETE CASCADE`) for the target URL, then re-inserts them.

### RAG Consistency Check (`db/rag_consistency.py`)

The check is implemented by `check_rag_consistency` in `scripts/db/rag_consistency.py`. Use it to detect trigger-based synchronization failures or orphaned records. Run this after bulk ingestion, after a forced re-registration, or during diagnostics.

**CLI:** `/session rag-consistency` runs the same check from the REPL and displays issues.

**Post-Ingestion Warning:** After `ingest_all()` completes, `ingester.py` runs a non-blocking consistency check via `DocumentManager.check_consistency()` (`scripts/rag/ingestion/document_manager.py`). Warnings are logged, but the ingestion process itself is not interrupted. If the check fails with `sqlite3.OperationalError`, `sqlite3.DatabaseError`, or `ValueError`, it returns `None` and the exception is not re-raised.

**Notes:**
- `fts` is read from `chunks_fts_docsize` (FTS5 shadow table), not `chunks_fts`. This provides an accurate count of FTS5 indexed documents without depending on joins with the backing table.
- `orphan_vec_count > 0` indicates a failure in the vec trigger. This can be fixed by re-running `ingester.py --force` for the affected URLs.
- This function is read-only and does not repair inconsistencies.
- Performance: The `NOT IN` subquery for orphan detection is O(vec × chunks). For large datasets, run this during maintenance windows.

### Additional Options for `crawler.py`

- `--targets-file PATH`: Specifies a TOML file in the `[[url, lang], ...]` format, overriding the `target_urls` in the configuration file (`config/crawler.toml`). Cannot be used with `--url` (exits with `parser.error`).

---


## Keywords

- configuration
