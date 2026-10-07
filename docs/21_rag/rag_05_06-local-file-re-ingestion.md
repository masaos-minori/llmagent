---
title: "6. Local file re-ingestion"
area: rag
tags:
  - rag
  - configuration
related:
  - rag_00_document-guide.md
  - rag_05_01-configuration-reference.md
---


# 6. Local file re-ingestion

## Initial Ingestion

```bash
# Run by adding file:// to target_urls
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
```

TOML format:
```toml
target_urls = [
    ["file:///path/to/file.py", "en"],
]
```

- Three-step process (separate processes): Crawling → Chunk Splitting → Embedding.
- `.py` files: Content is stored in `code_blocks`.
- `etag`: SHA-256 hash of file content (instead of HTTP ETag).
- `last_modified`: File mtime (ISO8601).

## Re-ingestion after file changes

The ingester compares the current file's SHA-256 hash with the `etag` stored in the `documents` table.

- **No changes** (hash matches): Automatically skipped; no re-ingestion occurs.
- **Changes detected** (hash differs): Automatically re-ingested — old documents and chunks are deleted, then re-chunked and re-embedded.
- **`--force`**: Deletes and re-ingests regardless of the hash.

Log messages during ingestion:

- `"file:// unchanged (sha256 match): file:///path/to/file"` — Skipped
- `"file:// changed — auto re-ingesting: file:///path/to/file"` — Re-ingested

## Batch re-ingestion of multiple local files

If multiple files have changed, run the crawler specifying `--targets-file` to re-crawl all listed `file://` URLs.
The crawler does not support `--force` and always writes the crawl payload; unchanged files are skipped at ingestion by the SHA-256 comparison in `DocumentManager`.
To force re-running embeddings for already ingested URLs, run `ingester.py --force` after crawling.

```bash
uv run python scripts/rag/ingestion/crawler.py --targets-file /path/to/targets.toml
uv run python scripts/rag/ingestion/ingester.py --force
```

## Comparison: Local Files vs. Web URLs

| Aspect | Web URL | Local File (file://) |
|---|---|---|
| Skipping when unchanged | Yes (ETag/304) | Yes (SHA-256 hash) |
| Forced re-indexing | `--force` | `--force` |

---


## Keywords

configuration
file-ingestion
crawler
etag
sha256
