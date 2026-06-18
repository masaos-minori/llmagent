# Implementation: Define Incremental Update Strategy for `file://` Ingestion — Ingestion Pipeline Doc

## Goal

Add a "Local file ingestion" subsection to `docs/03_rag_02_ingestion_pipeline.md` describing the crawl → chunk → ingest flow and the incremental update strategy (mtime + hash-based skip).

## Scope

- `docs/03_rag_02_ingestion_pipeline.md` — new section after §4 (RagIngester) or as a new §7

## Assumptions

1. The strategy defined in the plan is approved: mtime + SHA-256 hash of first chunk.
2. `documents.last_modified` already exists in schema (currently NULL for local files).
3. No schema changes are part of this design task (hash stored in crawl JSON only, not DB yet).

## Current State (to be documented)

### Local file crawl (`crawler.py:72-102`)

- `crawl_file(path, lang)` reads file content, writes JSON to `{rag_src_dir}/{timestamp}-{slug}.txt`
- Output fields: `url`, `title`, `lang`, `fetched_at`, `content`, `code_blocks`
- **Gap:** no mtime or hash stored in crawl output; `etag`/`last_modified` are NULL through the pipeline

### Chunk splitter (`chunk_splitter.py`)

- Reads crawl JSON, passes `etag` and `last_modified` through to chunk JSON (both NULL for local files)
- Chunks contain: `url`, `title`, `lang`, `source_file`, `chunk_index`, `chunk_type`, `content`, `normalized_content`, `etag`, `last_modified`

### Ingester (`ingester.py`)

- For local file URLs (`file://...`), accepts them alongside http/https
- `_get_or_create_document()`: if URL already in `documents`, skips (UPDATEs etag/last_modified only)
- For local files, etag/last_modified are always NULL → no incremental detection possible today

## Proposed Strategy (to document)

### Signal table

| Signal | Mechanism | Skip condition |
|---|---|---|
| **File mtime** | Store `file_mtime` in crawl JSON; ingester writes to `documents.last_modified` | If file mtime ≤ stored `last_modified`, skip URL group |
| **Content hash** (SHA-256 of first chunk text) | Compute in crawler or chunk splitter; store in crawl JSON and chunk JSON | If hash matches stored hash, skip URL group |

### Flow description

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐     ┌──────────┐
│  Local file  │────▶│  crawl_file()   │────▶│ chunk_split │────▶│  Ingester │
│  (path, lang)│     │ + mtime+hash    │     │              │     │ + skip chk│
└──────────────┘     └─────────────────┘     └──────────────┘     └──────────┘
                            │                          │                  │
                            ▼                          ▼                  ▼
                    {rag_src}/{ts}-{slug}.txt   {rag_src}/chunk/     SQLite documents
                    file_mtime, content_hash    (propagate both)     last_modified, hash_col
```

### Crawler changes (design only, not implemented)

**`crawl_file()` output JSON extension:**
```json
{
  "url": "file:///absolute/path/to/file.py",
  "title": "file.py",
  "lang": "en",
  "fetched_at": "2024-01-01T12:00:00",
  "content": "...",
  "code_blocks": ["..."],
  "file_mtime": "2024-01-01T10:00:00",
  "content_hash": "sha256:abcdef..."
}
```

**`crawl_file()` implementation sketch:**
```python
stat = path.stat()
payload["file_mtime"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
payload["content_hash"] = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"
```

### Ingester changes (design only, not implemented)

**`_get_or_create_document()` skip logic for local files:**
```python
# After SELECT documents WHERE url = ?
if existing:
    stored_mtime = existing["last_modified"]
    stored_hash = existing.get("content_hash")  # new column?
    
    if file_mtime <= stored_mtime and content_hash == stored_hash:
        return None  # skip — no change detected
    
    # Partial update: mtime changed but hash same (rename only)
    # Or: hash changed (content changed) → proceed with force-like behavior
```

### Difference from web ingestion

| Aspect | Web (`http://`) | Local (`file://`) |
|---|---|---|
| Freshness signal | HTTP `ETag` / `Last-Modified` headers + conditional GET | File system `mtime` + content SHA-256 hash |
| Skip mechanism | 304 Not Modified → skip file save | mtime ≤ stored + hash match → skip ingest |
| Trigger | Crawler runs on schedule | Operator runs `crawl_file()` + `ingester.py` |
| Hash computation | Not computed (HTTP headers suffice) | SHA-256 of full content (crawler) or first chunk |

## Implementation Steps (for future code implementation)

1. Add `file_mtime` and `content_hash` fields to crawl JSON output in `crawl_file()`
2. Propagate both fields through chunk splitter to chunk JSON
3. Extend `documents` table schema (new `content_hash TEXT` column) — migration needed
4. Update `_get_or_create_document()` to compare mtime + hash for local files
5. Add CLI flag `--check-only` to report stale files without ingesting

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Read updated doc | Strategy is clear, implementable, differences from web are explicit |
| Consistency check | Cross-reference with existing docs | No contradictions with §2.2 (conditional GET) or §4.2 (idempotency) |
