# Keep the crawl payload contract in one place on the freshness skip path

## Priority
Medium

## Summary
The crawler's 304 skip path writes a freshness-update payload with a `dict(...)`
constructor that duplicates — and can silently drift from — the strict
`CrawlJsonPayload` TypedDict, and `orchestrator.update_crawl_timestamp` re-implements
payload reading/writing outside `CrawlPersister`, the component that owns payload
construction. Move the skip-path payload handling into `CrawlPersister` typed against
`CrawlJsonPayload`.

## Problem
- `scripts/rag/ingestion/orchestrator.py` `crawl`'s 304 branch builds the updated payload
  with `dict(existing, fetched_at=now_iso(), lang=lang, content=...)`, a dynamic dict
  operation with no type checking against `CrawlJsonPayload`.
- `orchestrator.update_crawl_timestamp` reads `rag-src/{stem}.json`, parses it as a plain
  `dict`, mutates two fields, and writes it back with `orjson.dumps` — persistence logic
  living in the orchestration component.
- Meanwhile `CrawlPersister` (the declared owner of "JSON payload construction and write")
  has an unused-by-production method `save_conditional_meta` that would have used the
  strict `dict()`-constructor pattern, and its own `save_page` already centralizes
  `CrawlJsonPayload` construction.
- Consequence: the payload schema now has three write sites (save_page, the orchestrator
  304 branch, update_crawl_timestamp); a field added to `CrawlJsonPayload` is enforced in
  only one of them.

## Background
The orchestrator was extracted from WebCrawler with the freshness-skip behavior; the
timestamp update stayed as dict manipulation in the orchestrator while payload typing was
later centralized in `pipeline_utils.CrawlJsonPayload` (Phase 1 strict TypedDicts).

## Reason for Change
Schema drift risk: the chunk splitter and downstream stages validate payloads field by
field; an untyped writer that omits or misspells a field fails late (ChunkFormatError at
split time) instead of at the write site.

## Implementation Intent
Give `CrawlPersister` an explicit freshness-update method (e.g.
`update_fetched_at(url, content_hash, lang) -> bool`) that owns read-modify-write of the
rag-src payload typed as `CrawlJsonPayload`, and have the orchestrator call it instead of
manipulating dicts. Retire or fold in `save_conditional_meta` accordingly.

## Target Files or Areas
- `scripts/rag/ingestion/crawl_persister.py`
- `scripts/rag/ingestion/orchestrator.py`
- `tests/rag/ingestion/test_crawl_persister_lang.py`

## Required Changes
- Add the typed freshness-update method to `CrawlPersister`; remove
  `orchestrator.update_crawl_timestamp` and the inline `dict(existing, ...)` payload
  construction from the orchestrator.
- Validate the loaded payload against the `CrawlJsonPayload` field set (reuse or mirror
  `pipeline_utils` validation) before rewriting.
- Delete `save_conditional_meta` if the new method supersedes it.

## Constraints
- Preserve the skip-path content-hash matching rule (update only the payload matching
  `md5(content)`; do not resurrect the older `title = url.split('/')[-1]` comparison).
- Preserve `updated == 0` fallback behavior (no matching file → nothing written).
- Keep the `updated > 1` warning.

## Acceptance Criteria
- All writes to `rag-src/*.json` go through `CrawlPersister` methods typed against
  `CrawlJsonPayload`.
- A payload missing a required field triggers an error at the read-modify-write site,
  not later in the chunk stage.
- Existing skip-path behavior tests keep passing.

## Testing Expectations
- Unit tests for the new `CrawlPersister` method covering hash match, hash mismatch
  (updated == 0), and multi-match warning.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
N/A: no docs specify the internal payload write sites.

## Out of Scope
- Changing which URLs trigger the skip path.

## Dependencies
- N/A: none

## Unresolved Questions
- None.

## AI Implementation Instruction
Move, don't rewrite: keep the existing read-modify-write semantics, only relocate them
behind the typed `CrawlPersister` interface.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/orchestrator.py`
