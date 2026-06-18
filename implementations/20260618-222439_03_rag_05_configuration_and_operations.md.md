# Implementation: Define Incremental Update Strategy for `file://` Ingestion — Configuration & Operations Doc

## Goal

Add an operational workflow section to `docs/03_rag_05_configuration_and_operations.md` describing how operators re-ingest local files efficiently using the incremental update strategy.

## Scope

- `docs/03_rag_05_configuration_and_operations.md` — new subsection under §2 (Execution Guide)

## Assumptions

1. The mtime + hash strategy is documented in `03_rag_02_ingestion_pipeline.md` first.
2. This doc focuses on the operator workflow, not the technical design.

## Current State (to be documented)

### Today's local file ingestion workflow

```bash
# Step 1: Crawl a single local file
uv run python scripts/rag/ingestion/crawler.py --file /path/to/file.py --lang en

# Step 2: Chunk split
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-file.txt

# Step 3: Ingest
uv run python scripts/rag/ingestion/ingester.py
```

**Problem:** No incremental detection. If the file changed, the operator must either:
- Run `ingester.py --force` (deletes ALL existing records and re-ingests everything)
- Manually delete the crawl output and re-run (error-prone)

## Proposed Operational Workflow (to document)

### Incremental local file re-ingestion

```bash
# Step 1: Re-crawl changed files only (crawler detects mtime vs stored)
uv run python scripts/rag/ingestion/crawler.py --file /path/to/file.py --lang en

# Step 2: Chunk split (already idempotent; skips if chunks exist, --force to regenerate)
uv run python scripts/rag/ingestion/chunk_splitter.py --file /opt/llm/rag-src/20240101120000-file.txt

# Step 3: Ingest (ingester detects mtime+hash; skips unchanged files)
uv run python scripts/rag/ingestion/ingester.py
```

### Batch re-ingestion of all local files

```bash
# Re-crawl all local files in a directory
for f in /path/to/docs/*.py; do
    uv run python scripts/rag/ingestion/crawler.py --file "$f" --lang en
done

# Chunk split all
uv run python scripts/rag/ingestion/chunk_splitter.py

# Ingest (skips unchanged via mtime+hash comparison)
uv run python scripts/rag/ingestion/ingester.py
```

### Force re-ingestion (when needed)

```bash
# When content_hash detection fails or schema was updated
uv run python scripts/rag/ingestion/ingester.py --force
```

### Monitoring file freshness

```bash
# Check which local files are stale (mtime newer than DB last_modified)
# Future CLI: uv run python scripts/rag/ingestion/crawler.py --check-stale /path/to/docs/
```

## Configuration parameters (to add to §1.1 table)

| Parameter | Default | Description |
|---|---|---|
| `local_file_mtime_check` | `true` | Enable mtime-based incremental detection for `file://` URLs |
| `local_file_hash_check` | `true` | Enable SHA-256 content hash verification alongside mtime |

## Difference from web ingestion operations

| Operation | Web | Local |
|---|---|---|
| Trigger | Scheduled crawler (all target_urls) | Manual `--file` per file or batch loop |
| Skip detection | HTTP 304 (automatic, in-crawler) | mtime+hash comparison (at ingest time) |
| Force re-ingest | Re-run crawler (overwrites crawl JSON) | `ingester.py --force` or delete crawl JSON + re-run |
| Partial update | Not possible (HTTP is all-or-nothing) | Possible if only mtime changed (rename) vs hash changed (content) |

## Implementation Steps (for future code implementation)

1. Add `--check-stale` CLI flag to `crawler.py` — reports files where mtime > stored last_modified
2. Add `local_file_mtime_check` and `local_file_hash_check` config params to `rag_pipeline.toml`
3. Extend `documents` table with `content_hash TEXT` column (migration in `db/maintenance.py`)
4. Update `ingester.py._get_or_create_document()` to compare mtime+hash for local file URLs

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Manual review | Read updated doc | Operator workflow is clear and actionable |
| Consistency check | Cross-reference with §2.5 (`--force` behavior table) | New incremental workflow doesn't contradict existing force semantics |
