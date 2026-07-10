---
title: "2. Execution Guide"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_05_configuration_and_operations.md
---

# 2. Execution Guide

## 2. Execution Guide

### 2.1 Prerequisites

```bash
# Confirm embed-llm is running
curl -s http://127.0.0.1:8003/health

# Confirm config file is present (defines rag_src_dir, defaults to /opt/llm/rag-src)
ls -la config/rag_pipeline.toml
```

### 2.2 Step 1: Crawl

```bash
# All target_urls from config/rag_pipeline.toml
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &
tail -f logs/crawl.log

# Single URL
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# Multiple URLs (same --lang applied to all)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en
```

### 2.3 Step 2: Chunk split

```bash
# All unprocessed .json files in {rag_src_dir}/
uv run python scripts/rag/ingestion/chunk_splitter.py

# Single file (use absolute path from config)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.json

# Regenerate existing chunks (--force)
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### 2.4 Step 3: Embed and store

```bash
# Confirm embed-llm before running
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# Force re-register (delete and re-insert) existing URLs
uv run python scripts/rag/ingestion/ingester.py --force
```

### 2.5 `--force` behavior per script

| Script | `--force` effect |
|---|---|
| `crawler.py` | Not applicable (crawler always overwrites; idempotency via `visited` set per run) |
| `chunk_splitter.py` | Delete existing `{stem}-*.json` chunks and regenerate |
| `ingester.py` | Delete `chunks_vec` → `chunks` → `documents` records for the URL, then re-insert |

### 2.6 RAG Consistency Checks (`db/maintenance.py`)

Use `check_rag_consistency(db)` to detect trigger-based sync failures and orphan records.
Run after large ingestion, after force-reinsertion, or during diagnostics.

```python
from db.rag_consistency import RagConsistencyReport, check_rag_consistency, is_consistent, summarize_issues
from db.helper import SQLiteHelper

with SQLiteHelper("rag").open() as db:
    report: RagConsistencyReport = check_rag_consistency(db)
    if not is_consistent(report):
        for issue in summarize_issues(report):
            print(issue)
```

**`RagConsistencyReport` fields:**

| Field | Description |
|---|---|
| `chunks` | Row count in `chunks` table |
| `fts` | Indexed document count in `chunks_fts_docsize` shadow table |
| `vec` | Row count in `chunks_vec` table |
| `orphan_vec_count` | `chunks_vec` rows whose `chunk_id` has no matching row in `chunks` |
| `fts_gap` | `chunks - fts`; 0 = FTS index is in sync |
| `fts_orphan_count` | `fts - chunks`; positive = extra FTS entries (data loss risk) |
| `affected_chunk_ids` | chunk_ids missing from FTS (up to 10) |
| `affected_doc_ids` | doc_ids for chunks missing from FTS (up to 10) |
| `affected_orphan_chunk_ids` | chunk_ids in `chunks_vec` with no matching `chunks` row (up to 10) |
| `affected_orphan_urls` | URLs of documents with orphan vec rows (up to 10; `None` when no parent document can be resolved) |

**CLI:** `/db consistency` runs the same check from the REPL and prints issues.

**Post-ingest warning:** `ingester.py` runs a non-blocking consistency check after each `ingest_all()` run; warnings are logged but ingestion does not abort.

**Notes:**
- `fts` is read from `chunks_fts_docsize` (FTS5 shadow table), not from `chunks_fts` directly.
  This gives the true FTS5 indexed document count, independent of the backing table join.
- `orphan_vec_count > 0` indicates a vec trigger failure; repair by re-running `ingester.py --force`
  for the affected URL.
- This function is read-only; it does not repair inconsistencies.
- Performance: the `NOT IN` subquery in orphan detection is O(vec × chunks). Run during
  maintenance windows on large datasets.

---


## Related Documents

- [03_rag_05_configuration_and_operations.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
