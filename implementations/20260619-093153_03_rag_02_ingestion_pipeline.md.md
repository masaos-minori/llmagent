# Implementation: Document Local-File Ingestion Incremental Strategy

## Goal

Add a "Local file ingestion" subsection to `docs/03_rag_02_ingestion_pipeline.md` that:
- Describes the `crawl_file()` → chunk → ingest flow for `file://` URLs
- Defines the incremental update strategy (mtime + optional hash) so the next engineer can implement it without reverse-engineering the code
- Contrasts the approach with web ingestion (ETag/conditional GET)

## Scope

- `docs/03_rag_02_ingestion_pipeline.md` — new subsection for local-file ingestion with incremental strategy

Out of scope:
- Code implementation of mtime/hash checking
- DB schema changes
- CLI changes
- Watch mode

## Assumptions

1. `crawl_file()` currently writes the payload WITHOUT `etag` or `last_modified` fields (confirmed: `crawler.py` line 90-97).
2. The ingester's idempotency check skips by URL; if the URL already exists in `documents` it skips re-embedding — but does NOT check mtime/hash, so file changes go undetected unless `--force` is used.
3. `documents.last_modified` column already exists in the schema (used for HTTP `Last-Modified`; currently `NULL` for file:// URLs).
4. Strategy decision: use **both** mtime (fast) and SHA-256 hash of full content (reliable), with mtime as the primary filter. This matches the plan's proposed strategy table.

## Implementation

### Target file

`docs/03_rag_02_ingestion_pipeline.md`

### Procedure

1. Locate the existing `crawl_file` row in the API table (currently line 86) and confirm there is no local-file section below it.
2. After the conditional GET description (around line 102), insert a new `### Local file ingestion` subsection.
3. The subsection must cover:
   - The crawl flow: `crawl_file(path, lang)` → JSON written to `rag-src/` → `chunk_splitter` → `ingester`
   - Current limitation: no freshness check; file is always re-crawled
   - Proposed incremental strategy (documented for future implementation, not yet in code)
   - Comparison table: local file vs. HTTP/web

### Method

Insert a self-contained prose subsection with a strategy table. Use the existing doc style (headers, pipe tables, inline code).

### Details

**Subsection content outline:**

```
### Local file ingestion

`crawl_file(path, lang)` reads a local file and writes a crawl JSON to `rag-src/`.
Unlike web URLs, no HTTP round-trip occurs.

#### Current behavior (no freshness check)

crawl_file() always reads and rewrites the JSON regardless of file age.
The ingester skips re-embedding if the URL already exists in `documents`
(force=False). This means: if a file changes, the old embedding persists
until the operator runs ingestion with --force.

#### Proposed incremental strategy (not yet implemented)

| Signal        | Source           | Storage                | Skip condition                          |
|---------------|------------------|------------------------|-----------------------------------------|
| File mtime    | path.stat().st_mtime | documents.last_modified (ISO-8601) | mtime ≤ stored last_modified → skip |
| Content hash  | SHA-256 of full content | documents.etag (hex prefix "sha256:") | hash matches stored etag → skip |

Resolution order:
1. If mtime ≤ stored last_modified → skip (fast path)
2. Else compute SHA-256; if hash matches stored etag → skip (detects touch/chmod)
3. Else re-crawl, chunk, and re-embed

#### Contrast with web ingestion

| Aspect            | Web (HTTP)               | Local file (file://)         |
|-------------------|--------------------------|------------------------------|
| Freshness signal  | ETag / Last-Modified header | File mtime / SHA-256        |
| Skip mechanism    | 304 Not Modified         | Stored mtime or hash compare |
| Force re-index    | --force flag             | --force flag                 |
| current state     | Implemented              | Not yet implemented          |
```

### Note on design (step 1)

The strategy decisions are:
- **Both signals** (mtime + hash) — mtime is O(1) stat call; hash is O(file size) but definitive for files that are touched without content change.
- **Storage** — reuse existing `documents.last_modified` for mtime (ISO-8601 string from `datetime.fromtimestamp(mtime).isoformat()`) and `documents.etag` for hash (prefix `"sha256:"` to distinguish from HTTP ETags).
- **No DB schema change** — the existing columns absorb both signals.
- **CLI** — no new flag needed; existing `--force` bypass remains.

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the new subsection | strategy is clear and implementable without reading source |
| Consistency | Verify column names match `docs/06_shared_04_db_architecture_and_schema.md` | `last_modified`, `etag` column names confirmed |
