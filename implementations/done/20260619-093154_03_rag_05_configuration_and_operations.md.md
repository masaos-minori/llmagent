# Implementation: Document Local-File Re-ingestion Workflow in Operations Guide

## Goal

Add an operational workflow section to `docs/03_rag_05_configuration_and_operations.md` that explains how operators re-ingest local files efficiently, covering the current behavior (always re-crawls) and the future incremental path.

## Scope

- `docs/03_rag_05_configuration_and_operations.md` — new section for local-file re-ingestion workflow

Out of scope:
- Code changes
- Web URL re-ingestion (already covered in the doc)

## Assumptions

1. The current doc describes configuration parameters and general operations but has no local-file specific workflow section (confirmed: no mtime/incremental content found).
2. The target audience is an operator who runs ingestion commands, not a developer implementing the strategy.
3. The incremental strategy is not yet implemented; the doc must accurately distinguish current behavior from future behavior.

## Implementation

### Target file

`docs/03_rag_05_configuration_and_operations.md`

### Procedure

1. Read the current end of the doc to find the appropriate insertion point (likely after the web ingestion operations section or at the end).
2. Insert a new `## Local file re-ingestion` section.
3. Cover:
   - How to ingest a local file for the first time
   - What happens when the file changes (current: use --force; future: incremental)
   - The --force flag behavior
   - Recommended workflow for batch re-ingestion

### Method

New prose section with a command table and a workflow list. Use the existing doc style.

### Details

**Section content outline:**

```
## Local file re-ingestion

### First-time ingestion

Add the file path to `target_urls` in `rag_crawler.toml` with scheme `file://`:
  [[target_urls]]
  url = "file:///path/to/file.py"
  lang = "en"

Then run:
  /ingest run

The crawler calls `crawl_file()`, writes a JSON to `rag-src/`, chunks it,
and embeds it into the SQLite vector store.

### Re-ingesting after file changes

**Current behavior (no incremental check):**
If the file has changed, the ingester skips re-embedding because the URL
already exists in `documents` (force=False). To pick up changes:

  /ingest run --force

`--force` deletes the existing document and re-embeds all chunks from scratch.

**Future behavior (incremental — not yet implemented):**
Once the mtime/hash strategy is implemented, running `/ingest run` without
`--force` will detect changed files by comparing mtime and SHA-256 hash
against stored values. Unchanged files are skipped automatically.

### Batch re-ingestion of many local files

When multiple files change:
  /ingest run --force

All `file://` URLs in `target_urls` are re-crawled and re-embedded.
Use `--force` until the incremental strategy is available.

### Comparison: local files vs. web URLs

| Aspect           | Web URL                  | Local file (file://)         |
|------------------|--------------------------|------------------------------|
| Skip unchanged   | Yes (ETag/304)           | No (--force required now)    |
| Force re-index   | --force                  | --force                      |
| Future skip      | Already works            | Planned (mtime + hash)       |
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the new section | operator understands when to use --force and what changes in the future |
| Accuracy | Cross-check commands against `ingester.py` and `crawler.py` | command names and flags match actual CLI |
