## Goal
Fix `REQ-001`/`REQ-004` for `tests/rag/ingestion/test_ingester.py`: rewrite the 35 (of 36)
failing tests in `TestEmbedAndStore` and related classes so they call the post-split API
(`ChunkFactory._embed_and_store()` via a per-call `ChunkFactory` instance) instead of the
removed `RagIngester._embed_and_store()`.

## Scope
Modify exactly `tests/rag/ingestion/test_ingester.py`. No production code changes
(`scripts/rag/ingestion/*.py` are read-only references per the Plan's Out-of-Scope).

## Assumptions
- `patch.object(ingester._client, "post", ...)` (patching a method on the shared `httpx.Client`
  object) remains valid infrastructure after the split, because `RagIngester.__init__`
  (`scripts/rag/ingestion/ingester.py` line 104) and `EmbeddingService.__init__`
  (`scripts/rag/ingestion/embedding.py` line 38) both reference the *same* `httpx.Client`
  object — `RagIngester` passes its own `self._client` into `EmbeddingService`'s
  constructor. Only the direct `ingester._embed_and_store(doc_id, path)` calls are broken by
  the split (that method now lives on `ChunkFactory`, not `RagIngester`).
- The pre-fix baseline (`43 failed, 3 passed` across both target files) and this file's
  specific `35 of 36 failed` count are current as of this cycle's revalidation
  (`Confirmed by repository evidence`, re-run 2026-09-02).

## Design decisions
Per `skills/python-design/SKILL.md` Core Design Rules ("keep proposed design separate from
implemented behavior"): each failing test's `ingester._embed_and_store(doc_id, path)` call
must be replaced with one of two approaches, chosen per-test based on whether the test's
docstring/name describes unit-level `ChunkFactory` behavior or integration-level
`RagIngester` behavior:
1. Construct a `ChunkFactory(embedding_service, workers)` instance directly (mirroring
   `scripts/rag/ingestion/ingester.py` line 248's own construction:
   `ChunkFactory(self._embedding_service, self._embed_workers)`) and call its
   `_embed_and_store(...)` (confirmed at `scripts/rag/ingestion/chunk_preparation.py` line
   76) — for tests whose intent is clearly about the embed-and-store retry/error-handling
   logic itself (e.g. `test_embedding_failure_returns_false`, `test_retry_success`,
   `test_all_retries_exhausted`, `test_dimension_mismatch_on_retry`).
2. Drive the behavior through `RagIngester.ingest_url_group()` (the public entry point) and
   assert on its observable result — for tests whose intent is about end-to-end ingestion
   behavior rather than the retry mechanism in isolation.
- `patch.object(ingester._client, "post", ...)` does not need to change — the shared-object
  reference still holds (see Assumptions).

## Alternatives considered
- Patching `RagIngester._embed_and_store` via `patch.object(ingester, "_embed_and_store", ...)`:
  rejected — the method no longer exists on `RagIngester` at all (it moved to `ChunkFactory`),
  so there is nothing to patch; this would raise the same class of `AttributeError`.
- Rewriting every test as an integration test through `ingest_url_group()`: rejected as the
  sole approach — several tests specifically target retry/dimension-mismatch edge cases in
  the embed-and-store loop that are much harder to trigger reliably through the full
  ingestion pipeline; a per-test choice (per Design decisions above) is more faithful to each
  test's original intent (REQ-004).

## Implementation
### Target file
`tests/rag/ingestion/test_ingester.py`

### Procedure
For each of the 35 failing tests in this file (all reached via `ingester._embed_and_store(doc_id, path)`, confirmed by `grep -n "ingester._embed_and_store" tests/rag/ingestion/test_ingester.py`), replace the direct call per Design decisions above, preserving each test's existing assertions and `patch.object(ingester._client, "post", ...)` setup where present.

### Method
1. Read `scripts/rag/ingestion/chunk_preparation.py` in full to confirm `ChunkFactory`'s
   constructor signature (`__init__(self, embedding_service, workers)`, confirmed at line 25)
   and `_embed_and_store`'s signature (line 76) before rewriting any test.
2. For each failing test, construct `factory = ChunkFactory(ingester._embedding_service, ingester._embed_workers)` (or the equivalent already-visible collaborator names) immediately before the previously-failing call, and replace `ingester._embed_and_store(doc_id, path)` with `factory._embed_and_store(doc_id, path)` — unless the test's docstring/name indicates it should instead be restructured as an integration test through `ingester.ingest_url_group()` (apply per-test judgment per Design decisions).
3. Re-run the targeted test class after each batch of edits to confirm no new, different failure was introduced (per `skills/plan-to-implementation-procedure/workflow.md` Step 3's adversarial-verification spirit — don't assume the fix is complete without re-running).

### Details
Re-confirmed against current source (adversarial verification, this cycle):
- `uv run pytest tests/rag/ingestion/test_ingester.py -q` currently shows the failures this
  document fixes (part of the combined `43 failed, 3 passed` baseline across both target
  files in this Plan).
- `RagIngester.__init__` (`scripts/rag/ingestion/ingester.py` lines 91-114) holds
  `self._embedding_service` as its only persistent embedding-related collaborator attribute;
  `ChunkFactory` is constructed per-call (line 248), not stored as a `RagIngester` attribute
  — a rewritten test must construct its own `ChunkFactory` instance, it cannot reach one via
  `ingester._chunk_factory`.
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
Trivially revertable: `git checkout -- tests/rag/ingestion/test_ingester.py` restores the
original (failing) test bodies. No migration, no persisted state, no other file depends on
this change.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_ingester.py -v` — expect zero failures (REQ-001).
- `uv run pytest` (full suite) — no new failures vs. current baseline (REQ-002).
- `uv run ruff check tests/rag/ingestion/test_ingester.py && uv run mypy tests/rag/ingestion/test_ingester.py && uv run bandit -r tests/rag/ingestion/test_ingester.py` — clean (REQ-003).
- Manual review: confirm no test's original behavioral intent (per its name/docstring) was
  dropped or weakened (REQ-004).

## Completion criteria
All 36 tests in `tests/rag/ingestion/test_ingester.py` pass; no test's original assertions
were removed or weakened without an equivalent replacement; `ruff`/`mypy`/`bandit` report no
new issues.

## Out of scope
Any further refactoring of `RagIngester`, `EmbeddingService`, `ChunkFactory`, or
`TransactionManager` production code. `tests/rag/ingestion/test_rag_ingester.py` — covered
by a separate implementation procedure document (seq 02) for this same Plan.

## Documentation
`tests/rag/ingestion/test_ingester.py` has no matching row in `docs/00_index.md`'s "Document
References by Task" table — no `docs/*.md` update applies (Step 5: `N/A: no docs/00_index.md
task-scope mapping for tests/rag/ingestion/test_ingester.py`). Step 6 content checks skipped
accordingly.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `chunk_preparation.py`/`embedding.py`/`transaction_commit.py`/`document_persistence.py` in full | Completed | 2026-09-02 | 2026-09-02 | Discovered additional scope beyond this document's original text: `ingest_url_group()` gained a required `doc_store: DocumentStore` positional parameter, and `_insert_chunks_batch` moved to `TransactionManager` (not only `ChunkFactory._embed_and_store`/`ChunkFactory.prepare`) — both fixed in the same cycle |
| 2 | Rewrite the 35 failing tests per Method (expanded per Step 1's findings) | Completed | 2026-09-02 | 2026-09-02 | 11 `_embed_and_store` call sites → `ChunkFactory`; 18 `ingest_url_group` call sites → added `DocumentStore(...)` arg; 1 `_insert_chunks_batch` direct-call test → `TransactionManager`; 1 `_insert_chunks_batch` mock test → `patch.object(TransactionManager, ...)`; 4 `time.sleep` patch targets moved `rag.ingestion.ingester.time.sleep` → `rag.ingestion.embedding.time.sleep` |
| 3 | Run targeted and full-suite tests | Completed | 2026-09-02 | 2026-09-02 | All 36 tests in this file pass. Full suite (`-n auto`, unrelated collection errors ignored) shows ~274 failures both with and without this change (confirmed via `git stash` comparison, 275 failed/4993 passed on baseline vs 274 failed/5901 passed with this change) — pre-existing, environment-level parallel-execution instability unrelated to this row; no new failures attributable to this change |
| 4 | Run `ruff`/`mypy`/`bandit` | Completed | 2026-09-02 | 2026-09-02 | `ruff` clean; `mypy` 77 errors (down from 104 pre-existing baseline — no new errors, net improvement); `bandit` 73 Low-severity (pre-existing pattern, no High/Medium) |

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
- **Related target files**: `tests/rag/ingestion/test_ingester.py`
