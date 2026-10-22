# Fix the stale chunk-insert reference in the DB protocol document

## Priority
Medium

## Summary
Correct the reference to `RagIngester._insert_chunk()` in the DB protocol document and in the matching docstring in `scripts/db/store_protocols.py`; neither the method nor the cited module path exists.

## Background
Running the generic checks of the docs consistency checker on `docs/41_db/` (the new `db` domain) reports `db_05_api_and_operations-protocol-and-backend.md` referencing `_insert_chunk()`, which is not defined anywhere under `scripts/`. The document says the `chunk_insert` field set "intentionally matches `RagIngester._insert_chunk()` in `scripts/rag/ingestion/ingester.py`". Current source: `scripts/rag/ingestion/ingester.py` exists, but the chunk INSERT now lives in `TransactionManager._insert_chunks_batch()` in `scripts/rag/ingestion/transaction_commit.py`. The docstring of the `chunk_insert` protocol method in `scripts/db/store_protocols.py` carries the same stale note and also cites `rag/ingester.py`, which does not exist. Confirmed by `rg "_insert_chunk\b" scripts` and `uv run python tools/check_docs_consistency.py --domain db`.

## Problem
The documented consistency anchor between the protocol's field set and the ingester points to a removed method. Whether the field sets still match is not stated by evidence in the document.

## Reason for Change
The note tells callers to verify consistency with the ingester; a dangling reference makes that instruction impossible to follow and leaves an unverified claim in the design document.

## Implementation Intent
Verify whether the `chunk_insert` field set still matches the chunk INSERT used by ingestion. If it does, restate the relationship without naming a private method (responsibility level: the field set matches the ingestion chunk INSERT, which callers must keep in sync). If it does not, record the discrepancy as a Known Issue or Needs Confirmation item instead of asserting a match.

## Target Files or Areas
- `docs/41_db/db_05_api_and_operations-protocol-and-backend.md`
- `scripts/db/store_protocols.py` (docstring of the `chunk_insert` protocol method, comment only)

## Required Changes
- Compare the `chunk_insert` parameters with the columns inserted in the ingestion chunk INSERT and record the result.
- Reword the document sentence and the docstring note so they reference the current responsibility, not a removed method or nonexistent module path.

## Constraints
- Docstring edit only; no behavior change in `scripts/db/store_protocols.py`.
- Follow the docs content policy (no private symbol names or line numbers in documents).

## Acceptance Criteria
- `uv run python tools/check_docs_consistency.py --domain db` no longer reports `_insert_chunk()`.
- The document and the docstring state the same, evidence-backed relationship.
- Docs checkers, `ruff`, `mypy --no-namespace-packages scripts/`, and the DB tests pass.

## Testing Expectations
- `uv run python tools/check_docs_consistency.py --domain db`
- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`
- `uv run pytest tests/db -q` and `uv run ruff check scripts/`

## Documentation Impact
Yes: one sentence in the DB protocol document (intent and constraint of the field-set consistency), plus the matching docstring.

## Out of Scope
- Changing the protocol signature or the ingestion code, and the other three measured warnings (stdlib names).

## Dependencies
- Depends on the `db` domain registration of `tools/check_docs_consistency.py` (already applied).
- Sibling-issue check: no other open issue under `issues/` touches these files.

## Unresolved Questions
- Do the `chunk_insert` field set and the ingestion chunk INSERT still match? Not yet verified; the issue's first required change establishes it.

## AI Implementation Instruction
Verify before rewording; if the field sets differ, stop and report instead of asserting a match. Change only the named sentence and docstring note.

## Traceability
- **Workflow phase**: code-implementation
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261022-093304_plan.md
- **Source implementation procedure**: implementations/done/20261022-100147_01_tools_check_docs_consistency.py.md
- **Generated at**: 20261022-104122
- **Related target files**: docs/41_db/db_05_api_and_operations-protocol-and-backend.md, scripts/db/store_protocols.py
