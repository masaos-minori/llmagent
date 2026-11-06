# Crawler output filenames must be unique to prevent silent document overwrite

## Priority
High

## Summary
Make the crawl output path derivation collision-free so two distinct crawled documents can never resolve to the same JSON file and silently overwrite each other.

## Background
The crawler persists each crawled page as a JSON payload under `rag-src/`. The output name is produced by `CrawlPersister.make_crawl_filepath`, which formats `{ts}-{slug}.json`, where `{ts}` is a second-granularity timestamp and `{slug}` comes from `url_to_slug`, which truncates the URL-derived slug to 80 characters. `save_http` and `save` write with `path.write_bytes(orjson.dumps(...))` and never check whether the target already exists.

## Problem
The output name is not a unique key. Two different URLs that share an 80-character-or-longer common prefix, saved within the same wall-clock second, map to the identical path. The later `write_bytes` replaces the earlier file with no error, warning, or trace. Under concurrent BFS (`crawl_concurrency`) same-second saves across distinct pages are plausible, so documents can be silently lost during a multi-page crawl.

## Reason for Change
The corpus is the sole input to downstream embedding and retrieval; a silently overwritten document degrades the index with no error log and no easy recovery. The current scheme provides no uniqueness guarantee, and no test exercises the collision case.

## Implementation Intent
Give every crawl artifact a unique, filesystem-safe name. Derive uniqueness from the canonical URL itself (for example a short hash of the full normalized URL, or the untruncated slug) combined with the existing timestamp prefix, and keep the naming in `CrawlPersister`. Preserve the `.json` extension and the human-readable `{timestamp}-{label}` shape so existing manual workflows and `rag-src/` browsing are unaffected.

## Target Files or Areas
`scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/crawler_utils.py`, `tests/rag/ingestion/`

## Required Changes
- Make the output name unique per canonical URL (hash of the full URL or untruncated slug appended to the timestamp prefix), not dependent on an 80-character truncation.
- Do not rely on wall-clock seconds alone for uniqueness.
- Keep the resulting name filesystem-safe and ending in `.json`.
- Add a regression test asserting two distinct long-prefix URLs never collide and that both output files exist after a simulated save.

## Constraints
- Preserve the `{timestamp}-<label>.json` visual convention and `.json` extension.
- Names must remain valid on the deployed filesystem and within any downstream glob (`rag-src/**/*.json`).
- Do not change the payload contents or the `read_crawl_json` schema.

## Acceptance Criteria
- Two distinct URLs sharing an 80-character-or-longer common prefix produce two distinct output paths.
- A simulated concurrent save of many distinct URLs writes one file per URL with no overwrite.
- The new naming stays filesystem-safe and ends in `.json`.
- The regression test for the collision case passes.

## Testing Expectations
- Unit test for the uniqueness function with colliding 80-char-prefix pairs.
- Integration-style test saving several distinct URLs and asserting all files exist and are distinct.
- `ruff` / `mypy` clean on touched files.

## Documentation Impact
None required unless the output layout is documented elsewhere; if so, note only the uniqueness policy, not the implementation.

## Out of Scope
- Changing the JSON payload schema or fields.
- Changing where `rag-src/` is located.
- Robots.txt, crawl rate, or link-filtering policy.

## Dependencies
N/A: none

## Unresolved Questions
- Whether to prefer a URL hash (compact, fixed width) versus the untruncated slug (human-readable but longer). Implementation may choose; both satisfy uniqueness.

## AI Implementation Instruction
Do not touch payload construction or the ingest schema. Only change how the output filename is derived so it is unique per canonical URL. Keep it filesystem-safe and `.json`. Add a regression test for the 80-character-prefix collision case. Run `ruff` and `mypy` on the changed files.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073205
- **Related target files**: `scripts/rag/ingestion/crawl_persister.py`, `scripts/rag/ingestion/crawler_utils.py`
