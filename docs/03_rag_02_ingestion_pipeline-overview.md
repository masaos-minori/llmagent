---
title: "Ingestion Pipeline Overview and Execution"
category: rag
tags:
  - ingestion-pipeline
  - execution-guide
  - crawler
  - chunk-splitter
  - ingester
  - rag
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_query_pipeline.md
  - 03_rag_05_configuration_and_operations.md
source:
  - 03_rag_02_ingestion_pipeline.md
---

# RAG Ingestion Pipeline

- System overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_configuration_and_operations.md](03_rag_05_configuration_and_operations.md)

---

## 1. Execution Guide

### Prerequisites

```bash
curl -s http://127.0.0.1:8003/health   # confirm embed-llm is running
```

### Step 1: Crawl

```bash
# All target_urls from config/rag_pipeline.toml
nohup uv run python scripts/rag/ingestion/crawler.py > logs/crawl.log 2>&1 &
tail -f logs/crawl.log

# Single URL (with per-page language auto-detection)
uv run python scripts/rag/ingestion/crawler.py --url "https://ziglang.org/documentation/master/" --lang en

# Multiple URLs (same --lang applied to all)
uv run python scripts/rag/ingestion/crawler.py \
    --url "https://ziglang.org/documentation/master/" \
          "https://zig.guide/" \
    --lang en

# Per-page CJK-ratio language detection
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/page" --lang auto
```

# Load targets (http:// and file://) from a TOML file
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml

The targets TOML file format:
```toml
target_urls = [
    ["https://ziglang.org/documentation/master/", "en"],
    ["file:///opt/llm/scripts/rag/ingestion/crawler.py", "en"],
]
```

**Note:** All file paths (`rag_src_dir`) are resolved from `config/rag_pipeline.toml`. Production default: `/opt/llm/rag-src/`.

### Step 2: Chunk split

```bash
# All unprocessed .json files in {rag_src_dir}/
uv run python scripts/rag/ingestion/chunk_splitter.py

# Single file only (path relative to rag_src_dir)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-ziglang.json

# Regenerate existing chunks
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### Step 3: Embed and store

```bash
# Confirm embed-llm is running
curl -s http://127.0.0.1:8003/health

uv run python scripts/rag/ingestion/ingester.py

# Force re-register existing URLs
uv run python scripts/rag/ingestion/ingester.py --force
```

### File lifecycle

| Path | Created by | Format |
|---|---|---|
| `{rag_src_dir}/yyyymmddhhmmss-{slug}.json` | `crawler.py` | JSON (url, title, lang, fetched_at, content, code_blocks, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by) |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | `chunk_splitter.py` | JSON (url, title, lang, source_file, chunk_index, chunk_type, content, normalized_content, etag, last_modified, schema_version, artifact_type [ingestion-only], created_by, chunking_strategy) |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | `ingester.py` (moved from chunk/) | Same as chunk file |

> **Artifact format note:** All `.json` files listed above contain JSON payloads.
> Always parse with `orjson.loads()` or `json.loads()`. To inspect a file:
> ```
> python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"
> ```

Production config: `rag_src_dir = "/opt/llm/rag-src"`. The default value `rag-src` is used only when no config is present.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_ingestion_pipeline-crawler.md`
- `03_rag_02_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_ingestion_pipeline-ingester.md`
- `03_rag_02_ingestion_pipeline-utils.md`
- `03_rag_02_ingestion_pipeline-shared.md`
- `03_rag_02_ingestion_pipeline-ft5.md`
- `03_rag_03_query_pipeline.md`
- `03_rag_05_configuration_and_operations.md`

## Keywords

ingestion-pipeline
execution-guide
crawler
chunk-splitter
ingester
rag
