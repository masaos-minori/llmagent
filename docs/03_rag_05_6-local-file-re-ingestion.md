---
title: "6. Local file re-ingestion"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# 6. Local file re-ingestion

## 6. Local file re-ingestion

### First-time ingestion

Add the file path to `target_urls` in `config/rag_pipeline.toml` with scheme `file://`:

```toml
[[target_urls]]
url = "file:///path/to/file.py"
lang = "en"
```

Then run:

```
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

The crawler calls `crawl_file()`, writes a JSON to `rag-src/`, chunks it,
and embeds it into the SQLite vector store.

### Re-ingesting after file changes

The ingester compares the SHA-256 hash of the current file content against the
stored `etag` in `documents`:

- **Unchanged** (hash match): skipped automatically, no re-ingestion.
- **Changed** (hash differs): automatically re-ingested — delete old doc + chunks, re-chunk, re-embed.
- **`--force`**: delete and re-ingest regardless of hash.

Log messages during ingestion:

- `"file:// unchanged (sha256 match): file:///path/to/file"` — skipped
- `"file:// changed — auto re-ingesting: file:///path/to/file"` — re-ingested

### Batch re-ingestion of many local files

When multiple files change, run the crawler with `--targets-file` to re-crawl all listed `file://` URLs.
The crawler does not support `--force`; unchanged files are skipped automatically via SHA-256 hash comparison.
To force re-embedding of already-ingested URLs, run `ingester.py --force` after crawling:

```
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
uv run python scripts/rag/ingestion/ingester.py --force
```

### Comparison: local files vs. web URLs

| Aspect | Web URL | Local file (file://) |
|---|---|---|
| Skip unchanged | Yes (ETag/304) | Yes (SHA-256 hash) |
| Force re-index | `--force` | `--force` |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
