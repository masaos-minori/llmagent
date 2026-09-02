## Goal
Fix `REQ-001`/`REQ-004` for `tests/rag/ingestion/test_rag_ingester.py`: rewrite the 8 (of 10)
failing tests so they no longer patch `RagIngester._prepare_chunks` (moved to
`ChunkFactory.prepare()`) or rely on reassigning `ingester._client` to a mock object, which
no longer reaches the internal `EmbeddingService`'s HTTP calls.

## Scope
Modify exactly `tests/rag/ingestion/test_rag_ingester.py`. No production code changes
(`scripts/rag/ingestion/*.py` are read-only references per the Plan's Out-of-Scope).

## Assumptions
- The 8 currently-failing tests fail primarily via `patch.object(ingester, "_prepare_chunks", ...)`
  raising `AttributeError` (the attribute no longer exists on `RagIngester`), confirmed by
  the Plan's Problem statement and this cycle's re-run.
- `ingester._client = mock_http_client` (full reassignment, as opposed to
  `test_ingester.py`'s `patch.object(ingester._client, "post", ...)` pattern) does NOT raise
  `AttributeError` — `_client` still exists as a `RagIngester` attribute — but it is a latent,
  separate bug beyond the immediate test failures: `RagIngester.__init__`
  (`scripts/rag/ingestion/ingester.py` line 104) constructs `self._client`, then passes that
  *same object* into `EmbeddingService`'s constructor (line 106,
  `EmbeddingService(..., self._client)`), which stores it as its own `self._client`
  (`scripts/rag/ingestion/embedding.py` line 38). Reassigning `ingester._client = mock_http_client`
  *after* construction only changes `RagIngester`'s own reference — `EmbeddingService`'s
  already-bound reference to the original real `httpx.Client` is unaffected, so any HTTP
  call made through `EmbeddingService` would not be mocked. This must be fixed in the
  rewrite, not merely have its `AttributeError` symptom removed (part of REQ-004: preserve —
  do not silently weaken — each test's original mocking intent).

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("validate only at system boundaries";
"keep proposed design separate from implemented behavior"):
1. Replace `patch.object(ingester, "_prepare_chunks", ...)` with a patch on the
   `ChunkFactory.prepare` method (confirmed at `scripts/rag/ingestion/chunk_preparation.py`
   line 34) — since `ChunkFactory` is constructed per-call
   (`scripts/rag/ingestion/ingester.py` line 248), patch it at its import location,
   `rag.ingestion.ingester.ChunkFactory.prepare` (module-level patch), not on an
   `ingester`-owned attribute.
2. Replace `ingester._client = mock_http_client` with either: (a) constructing
   `RagIngester` with a config that lets the mock HTTP client reach `EmbeddingService`
   correctly (verify whether `RagIngester.__init__` accepts an injectable client — if not,
   patch `httpx.Client` at the module level before constructing `RagIngester` so
   `self._client` and `self._embedding_service._client` are both the mock from the start),
   or (b) patch methods directly on `ingester._embedding_service._client` (the object
   `EmbeddingService` actually uses), mirroring `test_ingester.py`'s working
   `patch.object(ingester._client, "post", ...)` pattern but targeting the embedding
   service's own client reference instead of `RagIngester`'s.

## Alternatives considered
- Leaving `ingester._client = mock_http_client` in place and only fixing the
  `_prepare_chunks` `AttributeError`: rejected — per Assumptions, this would silently leave
  the HTTP-mocking intent broken (tests would either make real network calls or fail with a
  different, confusing error later), which REQ-004 explicitly requires not to happen.
- Patching `ChunkFactory.prepare` via `patch.object(ingester, "_chunk_factory", ...)`:
  rejected — no such persistent attribute exists on `RagIngester` (see `test_ingester.py`'s
  companion procedure document, seq 01, Design decisions).

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`

### Procedure
For each of the 8 failing tests (`TestRagIngester::test_force_reinsert`,
`test_ingest_url_group_success[urls0]`, `test_ingest_url_group_success[urls1]`,
`TestCacheInvalidation::test_partial_success_cache_invalidation`,
`TestAtomicity::test_database_failure_during_replacement`,
`test_successful_replacement`, `test_partial_preparation_failure`,
`test_forced_reingest_with_embedding_failure` — confirmed via
`grep -n "class Test\|patch.object(ingester\|ingester._client" tests/rag/ingestion/test_rag_ingester.py`),
replace the `_prepare_chunks` patch target and the `ingester._client` reassignment per
Design decisions.

### Method
1. Read `scripts/rag/ingestion/chunk_preparation.py` (`ChunkFactory.prepare()`, line 34) and
   `scripts/rag/ingestion/embedding.py` (`EmbeddingService.__init__`, line 27; confirms the
   `_client` binding described in Assumptions) in full before rewriting.
2. Replace each `patch.object(ingester, "_prepare_chunks", ...)` with
   `patch.object(ChunkFactory, "prepare", ...)` (imported from
   `rag.ingestion.chunk_preparation` or patched via `rag.ingestion.ingester.ChunkFactory` —
   confirm which import path the test module already uses for `ChunkFactory`, if any, before
   choosing the patch target string).
3. Replace each `ingester._client = mock_http_client` / `ingester._client = MagicMock()`
   assignment with a patch that actually reaches `EmbeddingService`'s HTTP calls — either
   patching `ingester._embedding_service._client` directly (lowest-risk, mirrors the working
   `test_ingester.py` pattern), or constructing the mock client before `RagIngester(...)` is
   instantiated if the test needs the mock in place from construction time.
4. Re-run the targeted test class after each batch of edits to confirm the fix produces the
   originally-intended assertion result, not a new failure mode (e.g. a test asserting
   `ingester._client.post.assert_called_once_with(...)` must be updated to assert on
   whichever object actually receives the call after the fix).

### Details
Re-confirmed against current source (adversarial verification, this cycle):
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -q` currently shows the 8 failures
  this document fixes (part of the combined `43 failed, 3 passed` baseline across both
  target files in this Plan).
- `EmbeddingService.__init__` (`scripts/rag/ingestion/embedding.py` lines 27-38) stores
  `self._client = http_client` — confirming the shared-then-diverging reference described in
  Assumptions.
- No Plan-level inconsistency was found for this row beyond the already-corrected `Design`/
  `Risks` sections (see the Plan's own Traceability/Execution Status — corrected 2026-09-02
  during this cycle's Step 3).

## Compatibility considerations
N/A: test-only change; no public interface, schema, or runtime behavior changes.
`scripts/rag/ingestion/ingester.py`, `chunk_preparation.py`, and `embedding.py` are read-only
references, not modified.

## Security considerations
N/A: no security-relevant code path is touched; this is a unit/integration-test rewrite.

## Rollback considerations
Trivially revertable: `git checkout -- tests/rag/ingestion/test_rag_ingester.py` restores
the original (failing) test bodies. No migration, no persisted state, no other file depends
on this change.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` — expect zero failures (REQ-001).
- `uv run pytest` (full suite) — no new failures vs. current baseline (REQ-002).
- `uv run ruff check tests/rag/ingestion/test_rag_ingester.py && uv run mypy tests/rag/ingestion/test_rag_ingester.py && uv run bandit -r tests/rag/ingestion/test_rag_ingester.py` — clean (REQ-003).
- Manual review: confirm the `ingester._client` fix actually reaches `EmbeddingService`'s
  HTTP calls (e.g. by temporarily asserting the mock's call count is non-zero where the test
  expects a call) rather than merely silencing the `AttributeError` (REQ-004).

## Completion criteria
All 10 tests in `tests/rag/ingestion/test_rag_ingester.py` pass; the HTTP-client mocking
actually intercepts calls made through `EmbeddingService` (not merely through `RagIngester`'s
now-orphaned `_client` reference); no test's original assertions were removed or weakened
without an equivalent replacement; `ruff`/`mypy`/`bandit` report no new issues.

## Out of scope
Any further refactoring of `RagIngester`, `EmbeddingService`, `ChunkFactory`, or
`TransactionManager` production code. `tests/rag/ingestion/test_ingester.py` — covered by a
separate implementation procedure document (seq 01) for this same Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `chunk_preparation.py`/`embedding.py` in full | Pending | — | — | |
| 2 | Rewrite the 8 failing tests per Method | Pending | — | — | |
| 3 | Run targeted and full-suite tests | Pending | — | — | |
| 4 | Run `ruff`/`mypy`/`bandit` | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (fix stale-method test failures), REQ-004 (preserve behavioral intent)
- **Source issue**: `issues/20260901-161939_ingest001_test_ingester_stale_private_method_references.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-220527_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-110917
- **Related target files**: `tests/rag/ingestion/test_rag_ingester.py`
