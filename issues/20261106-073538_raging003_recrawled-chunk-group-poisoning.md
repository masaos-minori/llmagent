# Route or quarantine chunk groups that fail URL-group validation

## Priority
High

## Summary
`ChunkGroupingStrategy` groups chunk files purely by the payload `url` field, so chunk
files from two crawl generations of the same URL land in one group. When their shared
metadata (fetched_at, etag, source_file) differs, `ingest_url_group` fails with
`GROUP_VALIDATION_FAILED` and returns without routing any file — the group stays in
`rag-src/chunk/` forever and fails again on every subsequent run.

## Background
- `scripts/rag/ingestion/chunk_grouping.py` keys groups by `data.url` only.
- `scripts/rag/ingestion/ingester.py` `ingest_url_group` compares a 9-field signature
  (url, title, lang, fetched_at, etag, last_modified, source_file, chunking_strategy,
  chunk_type) across the group and returns a failure result with no `FileRouter` call
  when any file differs, or when `chunk_indices` are not exactly `range(len(files))`.
- `ChunkGroupingStrategy.group` also silently drops files whose payload fails
  `read_chunk_json` (they stay in `chunk/` unprocessed, with no log per file and no
  routing).
Coexistence scenario: the crawler runs twice (or a chunk run is re-executed) before the
ingester stage runs, leaving two generations of chunk files for one URL in `chunk/`. The
pipeline stages (`rag.ingestion.crawler` → `rag.ingestion.chunk_splitter` →
`rag.ingestion.ingester` per `deploy/setup_services.sh`) are separate manual invocations,
so the interleaving is operationally possible.

## Problem
A single malformed or multi-generation group becomes a permanent poison entry: every
ingester run re-processes it, logs the failure, counts it in totals, and never moves the
files out of `chunk/`. There is no operator-visible quarantine and no recovery path.

## Reason for Change
Broken workflow with growing operational cost: poisoned groups never leave the queue and
mask real progress metrics.

## Implementation Intent
Make group-validation failure terminal and visible: route the offending files through
`FileRouter` (failed/ with `.error.json` metadata, reason `group_validation_failed`)
instead of returning without routing, so the queue drains. Separately, make grouping
generation-safe so two crawl generations of one URL do not compete in one group — for
example group by (url, source_file) or validate per generation; decide the exact key
during planning.

## Target Files or Areas
- `scripts/rag/ingestion/ingester.py`
- `scripts/rag/ingestion/chunk_grouping.py`
- `scripts/rag/ingestion/file_routing.py`

## Required Changes
- On `validation_failure` and `GROUP_VALIDATION_FAILED`, route all group files to
  `FileRouter` as failed with the failure reason, so they leave `chunk/`.
- Route or quarantine files that `ChunkGroupingStrategy.group` skips (unreadable payload,
  empty or invalid url) instead of leaving them in `chunk/` silently.
- Choose and implement a grouping key that keeps distinct crawl generations in distinct
  groups (candidate: group by (url, source_file), keeping per-group index contiguity).

## Constraints
- Successful single-generation groups must keep their current URL-group semantics
  (one documents row per URL, all chunks ingested together).
- Keep `FileRouter` as the single routing point; do not add a second move mechanism.
- Do not change the per-field signature validation rules themselves.

## Acceptance Criteria
- After one ingester run, no chunk file for a validation-failed group remains in
  `rag-src/chunk/`; each file appears under `failed/` with `.error.json` metadata naming
  the group reason.
- Two generations of chunk files for the same URL no longer merge into one failing group;
  each generation is ingested or failed independently.
- Grouping skips (invalid url, unreadable payload) leave the input queue via routing or a
  documented quarantine with a per-file log line.

## Testing Expectations
- Regression tests: two-generation group (different fetched_at) — assert both generations
  resolve independently; malformed file — assert it is routed out and logged.
- Re-run idempotency test: a second `ingest_all` after a failed group reports zero
  re-processing of the failed files.
- `uv run pytest tests/rag/ingestion`.

## Documentation Impact
Document the queue lifecycle (chunk/ → registered/, retry/, failed/) at the intent level
in the RAG ingestion docs, including what a `group_validation_failed` entry means
operationally.

## Out of Scope
- Consuming `retry/` (tracked by `20261106-073538_raging005_retry-dir-no-consumer.md`).
- Crawler scheduling to prevent two generations before ingestion.

## Dependencies
- None at filing time; ordering note: this issue should land before or together with any
  retry/ consumption design (`20261106-073538_raging005_retry-dir-no-consumer.md`).

## Unresolved Questions
- Preferred grouping key (url-only with generation detection, or url+source_file) —
  confirm during planning against existing `registered/` expectations.
- Whether a group with mixed generations should ever ingest the newest generation
  automatically, or always require explicit operator action.

## AI Implementation Instruction
Keep routing changes inside `FileRouter` usage; do not move files ad hoc in the
ingester. Decide the grouping key explicitly in the plan before coding and cover both the
multi-generation and the malformed-file cases with tests.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/chunk_grouping.py`, `scripts/rag/ingestion/file_routing.py`
