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

| Path | Created By | Content |
|---|---|---|
| `{rag_src_dir}/{timestamp}-{slug}.json` | crawler.py | URL, Title, Language, Content, Code Blocks |
| `{rag_src_dir}/chunk/{stem}-{idx:04d}.json` | chunk_splitter.py | Chunk information, Strategy |
| `{rag_src_dir}/registered/{stem}-{idx:04d}.json` | ingester.py | Chunk → Registered |

> JSON files are parsed using `orjson.loads()`. For verification: `python -c "import orjson; print(orjson.loads(open('FILE', 'rb').read()))"`

Production setting: `rag_src_dir = "/opt/llm/rag-src"`. The default value `rag-src` is used only if no configuration is provided.

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_08_ingestion_pipeline-shared.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

ingestion-pipeline
execution-guide
crawler
chunk-splitter
ingester
rag
