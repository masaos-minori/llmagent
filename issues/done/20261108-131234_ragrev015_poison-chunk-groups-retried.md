# Chunk groups that fail at embedding or commit are retried on every ingest run

## Priority
Medium

## Summary
The ingester does not validate the embedding dimension against the vector column, and a `sqlite3.Error` raised during the commit is caught only at the top of the group loop without routing the chunk files to the failed directory, so a group that can never succeed is re-embedded and fails again on every run.

## Background
Review finding F-015 (Confidence Medium: the missing dimension check was confirmed by reading `scripts/rag/ingestion/embedding.py`, the other triggers are Strongly implied). Evidence: `embedding.py` `get_embedding` returns the vector without comparing its length to the `chunks_vec` dimension and without checking consistency across the batch; `TransactionManager.commit` inserts `pc.chunk_type` and the vector as given, so a dimension mismatch or a `chunk_type` outside the schema `CHECK (chunk_type IN ('text','code'))` surfaces as `sqlite3.Error`/`IntegrityError` from the transaction; `RagIngester._process_url_groups` logs it and returns without calling `FileRouter`. The archived issues `issues/done/20261106-073538_raging003_recrawled-chunk-group-poisoning.md` and `issues/done/20261106-073538_raging005_retry-dir-no-consumer.md` covered group validation and the retry directory, not this commit-time path.

## Problem
An embedding model change, a bad payload or a schema-violating chunk produces a permanent per-run cost (one embedding call per chunk) and an ever-growing failure log, and good groups behind it are unaffected only because the failure is contained.

## Reason for Change
The failure is deterministic, so retrying cannot help; the run should quarantine the group and report it.

## Implementation Intent
Validate the embedding length and `chunk_type` before the transaction, and route a group that fails deterministically at commit to the failed directory with the reason, while keeping transient errors retryable.

## Target Files or Areas
- `scripts/rag/ingestion/embedding.py`
- `scripts/rag/ingestion/ingester.py` (`ingest_url_group`, `_process_url_groups`)
- `scripts/rag/ingestion/chunk_grouping.py` (`read_chunk_json`)
- `scripts/rag/ingestion/file_routing.py`
- `tests/rag/ingestion/`

## Required Changes
- Compare each embedding length with the configured vector dimension and reject mismatches before the transaction.
- Validate `chunk_type` when reading chunk files.
- Classify commit errors into deterministic (route to failed) and transient (keep).
- Add tests for a wrong-size vector, an empty `chunk_type` and an integrity error.

## Constraints
- Keep the transaction atomic and the database consistent on failure.
- Do not add a new retry mechanism.

## Acceptance Criteria
- A group with a wrong-dimension embedding is moved to the failed directory with a reason and is not retried on the next run.
- A transient database error keeps the files in place.
- An empty or unknown `chunk_type` is rejected at read time.

## Testing Expectations
- Unit tests with a stub embedding client and an in-memory database.
- ruff and mypy on touched files.

## Documentation Impact
Document how deterministic ingest failures are routed (failure behavior) if the ingestion description lists the directories.

## Out of Scope
- Consuming the retry directory (archived issue).
- Changing the embedding retry policy.

## Dependencies
N/A: none (history only: `issues/done/20261106-073538_raging005_retry-dir-no-consumer.md`).

## Unresolved Questions
Whether `chunk_type == ""` can actually be produced by `ChunkSplitter` (the reader accepts it) and the exact exception types raised by sqlite-vec for a wrong dimension are `Needs confirmation`.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131234
- **Related target files**: `scripts/rag/ingestion/embedding.py`, `scripts/rag/ingestion/ingester.py`, `scripts/rag/ingestion/chunk_grouping.py`, `scripts/rag/ingestion/file_routing.py`, `tests/rag/ingestion/`
