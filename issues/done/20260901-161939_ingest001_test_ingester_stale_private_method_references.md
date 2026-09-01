# RagIngester ingestion-split tests still call/patch removed private methods

## Priority
High

## Summary
`tests/rag/ingestion/test_ingester.py` and `tests/rag/ingestion/test_rag_ingester.py`
call or `patch.object` private methods (`_embed_and_store`, `_prepare_chunks`, and
likely others) that no longer exist on `RagIngester` after the ingestion-split
refactor moved them into `EmbeddingService`/`ChunkFactory`. 43 tests across the two
files fail at runtime with `AttributeError`, even though the module now imports
cleanly.

## Background
`issues/done/20260829-080925_refactor_003_ingester_separation.md` (see also
`docs/00_governance_...` history) split `scripts/rag/ingestion/ingester.py`'s
`RagIngester` into dedicated collaborators: `EmbeddingService.embed_and_store()`
(`scripts/rag/ingestion/embedding.py`), `ChunkFactory.prepare()` /
`ChunkFactory._embed_and_store()` (`scripts/rag/ingestion/chunk_preparation.py`), and
`TransactionManager.commit()` (`scripts/rag/ingestion/transaction_commit.py`). The
split also introduced a `PreparedChunk` DTO that was never added to
`rag/models_data.py` — discovered and fixed separately (see the commit that
resolves this) alongside `ChunkFactory.__init__`'s `embed_service: object` parameter
typed too loosely for `mypy` to check the `.embed_and_store()` call. Fixing those two
issues (to unblock a `pre-commit` `mypy` failure unrelated to this issue) made the two
test files' `from rag.ingestion.ingester import ... PreparedChunk ...` imports
resolvable again (via a corrected import of `PreparedChunk` from `rag.models_data`),
which is what surfaced this issue: the tests import successfully now, but fail at
runtime because they still assume the pre-split `RagIngester` API surface.

## Problem
- `tests/rag/ingestion/test_ingester.py`: 35 of 36 tests fail. Representative
  failure: `AttributeError: 'RagIngester' object has no attribute '_embed_and_store'`
  (that method now lives on `ChunkFactory`/`EmbeddingService`).
- `tests/rag/ingestion/test_rag_ingester.py`: 8 of 10 tests fail. Representative
  failure: `AttributeError: <RagIngester object> does not have the attribute
  '_prepare_chunks'` (raised by `unittest.mock.patch.object`, which requires the
  attribute to exist to patch it; `_prepare_chunks` now lives on `ChunkFactory
  .prepare()`).
- Both files also directly construct `ingester._client = mock_http_client` and
  similar collaborator-internals assignments that assume `RagIngester` still owns
  the HTTP client / embedding logic directly, rather than delegating to
  `EmbeddingService`.

## Reason for Change
`refactor_003_ingester_separation`'s own Acceptance Criteria required existing
tests to keep passing (post-split behavior preservation) — that requirement was not
met for these two files. Left unfixed, ~43 tests provide false assurance: they were
silently uncollectable (`ImportError` on `PreparedChunk`) until this issue's
prerequisite fix restored collection, at which point the deeper breakage became
visible. Without this fix, `RagIngester`'s ingestion-split behavior (embedding,
chunk preparation, atomic commit, cache invalidation, force-reinsert) has no passing
test coverage.

## Implementation Intent
Update both test files to exercise the post-split API surface instead of
`RagIngester`'s removed private methods:
- Tests currently calling `ingester._embed_and_store(doc_id, path)` directly should
  either construct an `EmbeddingService`/`ChunkFactory` and call
  `embed_service.embed_and_store(...)` / `chunk_factory._embed_and_store(...)`, or
  restructure as an integration-style test that drives the behavior through
  `RagIngester`'s current public entry point (e.g. `ingest_url_group()`) and asserts
  on its observable result instead of reaching into a removed private method.
- Tests using `patch.object(ingester, "_prepare_chunks", ...)` (or similar) should
  patch the corresponding method on the `ChunkFactory` instance `RagIngester` now
  holds, not on `RagIngester` itself.
- Tests directly assigning to `ingester._client` (or other moved fields) should
  either construct the real `EmbeddingService`/`ChunkFactory` collaborators with a
  mock HTTP client, or patch/mock at the collaborator boundary `RagIngester` now
  uses to reach them.
- Confirm `RagIngester`'s current `__init__` signature and attribute names (which
  collaborator instances it holds, under what attribute names) before rewriting —
  do not guess.

## Target Files or Areas
- `tests/rag/ingestion/test_ingester.py`
- `tests/rag/ingestion/test_rag_ingester.py`
- `scripts/rag/ingestion/ingester.py` (read-only reference for current API)
- `scripts/rag/ingestion/embedding.py`, `scripts/rag/ingestion/chunk_preparation.py`,
  `scripts/rag/ingestion/transaction_commit.py` (read-only reference for current
  collaborator API)

## Required Changes
- Rewrite each of the 43 currently-failing tests to target the current
  `RagIngester`/`EmbeddingService`/`ChunkFactory`/`TransactionManager` API surface.
- Do not weaken assertions merely to make a test pass — preserve each test's
  original intent (embedding retry behavior, partial-failure routing, atomic
  commit, cache invalidation, force-reinsert) against the new API shape.
- Confirm no other test file in `tests/rag/` (or elsewhere) has the same stale
  reference to a removed `RagIngester` private method — a full-repo `rg` sweep for
  `_embed_and_store`, `_prepare_chunks`, `._client` on `RagIngester` instances is
  in scope for verifying completeness, not just fixing the two files named above.

## Constraints
N/A: none beyond the standard validation sequence.

## Acceptance Criteria
- `uv run pytest tests/rag/ingestion/test_ingester.py tests/rag/ingestion/test_rag_ingester.py -v` passes with zero failures.
- `uv run pytest` (full suite) shows no new failures compared to the current baseline.
- `ruff`, `mypy`, and `bandit` remain clean on both modified test files.
- No test's original behavioral intent (per its name/docstring) was silently dropped or weakened during the rewrite.

## Testing Expectations
Run the full standard validation sequence (`rules/toolchain.md`) after the rewrite,
plus the full `uv run pytest` suite once to confirm no regression elsewhere.

## Documentation Impact
N/A: test-only fix, no `docs/*.md` file describes this internal test structure.

## Out of Scope
- Any further refactoring of `RagIngester`, `EmbeddingService`, `ChunkFactory`, or
  `TransactionManager` production code — this issue is test-only.
- Re-opening `refactor_003_ingester_separation`'s own design decisions.

## Dependencies
N/A: none. Prerequisite fix (adding `PreparedChunk` to `rag/models_data.py` and
typing `ChunkFactory.__init__`'s `embed_service` parameter as `EmbeddingService`)
already landed separately, ahead of this issue, to unblock an unrelated `mypy`
pre-commit failure — this issue covers only the test-file rewrite that fix's import
correction surfaced as a follow-on need.

## Unresolved Questions
- Whether any of the 43 tests are better restructured as integration tests against
  `RagIngester`'s current public entry point rather than unit tests against an
  individual collaborator — left to implementation planning to decide per test.

## AI Implementation Instruction
- Read `scripts/rag/ingestion/ingester.py`, `embedding.py`, `chunk_preparation.py`,
  and `transaction_commit.py` in full before rewriting any test — do not infer the
  current API from the old test code.
- Preserve each test's original behavioral intent; do not delete a test merely
  because it is inconvenient to adapt.
- Run the full `rg` sweep for stale private-method references before declaring this
  issue resolved.
