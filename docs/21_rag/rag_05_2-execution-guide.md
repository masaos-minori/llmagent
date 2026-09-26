---
title: "2. Execution Guide"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_1-configuration-reference.md
source:
  - rag_05_1-configuration-reference.md
---


# 2. Execution Guide

## 2.1 Prerequisites

```bash
# Ensure embed-llm is running
curl -s http://127.0.0.1:8081/health

# Verify configuration files exist (defines rag_src_dir; default is /opt/llm/rag-src)
ls -la config/crawler.toml config/chunk_splitter.toml config/ingester.toml
```

## 2.2 Step 1: Crawling

```bash
# Crawl all URLs specified in crawler.toml
uv run python scripts/rag/ingestion/crawler.py

# Crawl a single URL
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/" --lang en
```

## 2.3 Step 2: Chunk Splitting

```bash
# Batch split unprocessed files
uv run python scripts/rag/ingestion/chunk_splitter.py

# Regenerate existing chunks
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

## 2.4 Embedding and Storage

```bash
# Embed and save to DB
uv run python scripts/rag/ingestion/ingester.py

# Force re-registration
uv run python scripts/rag/ingestion/ingester.py --force
```

### `--force` Behavior

- `crawler.py`: Not applicable (idempotent).
- `chunk_splitter.py`: Deletes existing chunks and regenerates them.
- `ingester.py`: Deletes `chunks_vec` $\rightarrow$ `chunks` $\rightarrow$ `documents` for the target URL, then re-inserts them.

### 2.6 RAG Consistency Check (`db/rag_consistency.py`)

> **Correction:** This section's heading was previously "`db/maintenance.py`", but the actual implementations of `check_rag_consistency`, `is_consistent`, and `summarize_issues` are defined in `scripts/db/rag_consistency.py`. They do not exist in `db/maintenance.py`.
> [Explicit in code]

Use `check_rag_consistency(db, embed_failed=0)` to detect trigger-based synchronization failures or orphaned records. Run this after bulk ingestion, after a forced re-registration, or during diagnostics.

```python
from db.rag_consistency import check_rag_consistency, is_consistent, summarize_issues
from db.models import RagConsistencyReport
from db.helper import SQLiteHelper

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

**`RagConsistencyReport` Fields** (Defined in `db/models.py`):

See `RagConsistencyReport` in `scripts/db/models.py` for exact fields.

**CLI:** `/session rag-consistency` runs the same check from the REPL and displays issues (the old `/db consistency` is deprecated; see `cmd_session.py`).

**Post-Ingestion Warning:** After `ingest_all()` completes, `ingester.py` runs a non-blocking consistency check via `DocumentManager.check_consistency()` (`scripts/rag/ingestion/document_manager.py`). Warnings are logged, but the ingestion process itself is not interrupted. If the check fails with `sqlite3.OperationalError`, `sqlite3.DatabaseError`, or `ValueError`, it returns `None` and the exception is not re-raised. [Explicit in code]

**Notes:**
- `fts` is read from `chunks_fts_docsize` (FTS5 shadow table), not `chunks_fts`. This provides an accurate count of FTS5 indexed documents without depending on joins with the backing table.
- `orphan_vec_count > 0` indicates a failure in the vec trigger. This can be fixed by re-running `ingester.py --force` for the affected URLs.
- This function is read-only and does not repair inconsistencies.
- Performance: The `NOT IN` subquery for orphan detection is $O(\text{vec} \times \text{chunks})$. For large datasets, run this during maintenance windows.

### 2.7 Additional Options for `crawler.py`

- `--targets-file PATH`: Specifies a TOML file in the `[[url, lang], ...]` format, overriding the `target_urls` in the configuration file (`config/crawler.toml`). Cannot be used with `--url` (`exits with `parser.error`).
  [Explicit in code] — From the `main()` argument definition in `scripts/rag/ingestion/crawler.py`.

---


## Related Documents

- [rag_05_1-configuration-reference.md](rag_05_1-configuration-reference.md)

## Keywords

configuration
