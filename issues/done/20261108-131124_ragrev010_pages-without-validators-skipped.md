# Pages served without ETag or Last-Modified are never re-ingested

## Priority
High

## Summary
`DocumentManager.handle_existing_document` treats an HTTP document as unchanged when the stored and incoming `etag` and `last_modified` are equal, and two `None` values compare equal, so a page whose server sends neither header is skipped forever after its first ingestion.

## Background
Review finding F-004. Evidence (Explicit in code): `scripts/rag/ingestion/document_manager.py` `handle_existing_document`, HTTP branch: `if stored["etag"] == etag and stored["last_modified"] == last_modified: return existing_doc_id, True, False`. The file-based path guards this case in `_is_file_unchanged`, which returns False when either side is `None`; the HTTP branch has no such guard. Existing tests cover the file guard (`tests/` freshness tests) but none covers the HTTP branch with both values `None`. Related archived work: `issues/done/20261106-073538_raging002_etag-updated-before-reingestion.md` (freshness write placement), which does not address this comparison.

## Problem
Sites without validators (static hosts, some documentation generators) are crawled once and never updated in the corpus, even when their content changes. Only a forced run repairs them.

## Reason for Change
The corpus silently goes stale for exactly the sources that give the crawler no other change signal.

## Implementation Intent
Decide the freshness rule for pages with no validators (treat absence as "unknown, re-ingest", or compare a content hash) and apply it in one place shared by the HTTP and file paths.

## Target Files or Areas
- `scripts/rag/ingestion/document_manager.py` (`handle_existing_document`, `_is_file_unchanged`)
- `scripts/rag/ingestion/etag_manager.py`
- `tests/rag/ingestion/` freshness tests

## Required Changes
- Do not treat two absent validators as equality.
- Choose the fallback signal (always re-ingest, or content hash) and document it.
- Add tests for the HTTP branch with `None`/`None`, one-sided `None`, and equal non-null values.

## Constraints
- Keep the 304 conditional-request behavior for pages that do send validators.
- Avoid re-embedding unchanged content when a content hash is available.

## Acceptance Criteria
- A page with no validators and changed content is re-ingested on the next run.
- A page with equal non-null validators is still skipped.
- The file and HTTP branches share the same absence rule.

## Testing Expectations
- Unit tests for `handle_existing_document` (HTTP) covering the three cases.
- ruff and mypy on touched files; `uv run pytest tests/rag -q`.

## Documentation Impact
Update the ingestion freshness description (intent and failure behavior) if it states that validators are required for change detection.

## Out of Scope
- Changing the crawler fetch logic.
- The file:// freshness rule (already guarded).

## Dependencies
N/A: none

## Unresolved Questions
Which fallback signal is acceptable for the embedding cost (always re-ingest versus content hash) is `Needs confirmation` and needs an owner decision.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131124
- **Related target files**: `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/etag_manager.py`, `tests/rag/ingestion/`
