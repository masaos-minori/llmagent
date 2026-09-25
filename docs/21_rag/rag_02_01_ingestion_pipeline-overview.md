---
title: "Ingestion Pipeline Overview and Execution"
area: rag
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
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---


# RAG Ingestion Pipeline

- System Overview → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- Configuration → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 1. Execution Guide

### Prerequisites

```bash
curl -s http://127.0.0.1:8081/health
```

### Step 1: Crawling

```bash
# Crawl all URLs from crawler.toml
uv run python scripts/rag/ingestion/crawler.py

# Crawl a single URL
uv run python scripts/rag/ingestion/crawler.py --url "https://example.com/" --lang en
```

- `--lang`: `auto` for automatic language detection, or specify `en`/`ja`.
- `--targets-file PATH`: Load target URLs from a TOML file.

### Step 2: Chunk Splitting

```bash
# Batch split unprocessed files
uv run python scripts/rag/ingestion/chunk_splitter.py

# Regenerate existing chunks
uv run python scripts/rag/ingestion/chunk_splitter.py --force
```

### Step 3: Embedding and Storage

```bash
# Embed and save to DB
uv run python scripts/rag/ingestion/ingester.py

# Force re-registration
uv run python scripts/rag/ingestion/ingester.py --force
```

### File Lifecycle

| Path | Created By | Content | Deletion Policy |
|---|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks | Deleted after successful chunking (no audit trail required) |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | chunk_splitter.py | Chunk information, Strategy | Deleted after successful ingestion (no audit trail required) |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | Chunk → Registered | Configurable retention via `config/ingester.toml`; default 30 days; cleanup mechanism design out of scope — requires separate design decision |

> **Retention configuration:** The retention period for `rag-src/registered/` files is configurable via `config/ingester.toml`. The default retention period is 30 days. Operations teams should review and adjust this value periodically based on their specific operational requirements (audit trail vs. disk space). If compliance requirements mandate indefinite retention, update this value accordingly.
>
> **Cleanup mechanism:** Automated cleanup of `rag-src/registered/` files requires a separate design decision. Options include operator intervention (manual cleanup), periodic task integrated into existing scheduling (if/when cron infrastructure is added), or on-ingestion cleanup triggered by `RagIngester` itself. This is explicitly out of scope for this issue.
>
> **JSON verification:** Parse crawl/chunk artifacts with `orjson.loads()` (the ingestion pipeline uses `orjson.dumps()` for writing and `orjson.loads()` for reading). Example — verify a crawl artifact:
>
> ```bash
> python -c "import orjson; print(orjson.loads(open('{rag_src_dir}/{timestamp}-{slug}.json', 'rb').read()))"
> ```
>
> Use the artifact path format from the table above (e.g., `{rag_src_dir}/20260913-183000_example.json`). The `'rb'` (binary read) mode is required because `orjson.loads()` accepts `bytes` input directly, matching how `read_crawl_json()`/`read_chunk_json()` read files via `path.read_bytes()` before passing to `orjson.loads()`. `orjson` is used instead of the standard `json` module for its performance characteristics (Rust-backed, significantly faster). Expected output: a Python `dict` printed to stdout, or a `json.JSONDecodeError` if the file is not valid JSON.
>
> **Crawl artifact keys:** `url`, `content`, `title`, `lang`, `code_blocks`, `etag`, `last_modified`, `fetched_at`
>
> **Chunk artifact keys:** additionally includes `normalized_content`, `chunk_index`, `source_file`, `chunk_type`, `chunking_strategy`

Production setting: `rag_src_dir = "/opt/llm/rag-src"`. The default value `rag-src` is used only if no configuration is provided.

---

## Related Documents

- `rag_00_document-guide.md`
- `rag_01_system_overview.md`
- `rag_02_02_ingestion_pipeline-crawler.md`
- `rag_02_03_ingestion_pipeline-chunksplitter.md`
- `rag_02_04_ingestion_pipeline-ingester.md`
- `rag_02_07_ingestion_pipeline-utils.md`
- `rag_02_08_ingestion_pipeline-shared.md`
- `rag_03_01_query_pipeline-overview.md`
- `rag_05_1-configuration-reference.md`

## Keywords

ingestion-pipeline
execution-guide
crawler
chunk-splitter
ingester
rag
