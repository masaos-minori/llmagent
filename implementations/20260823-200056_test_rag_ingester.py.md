## Goal
Update `tests/rag/ingestion/test_rag_ingester.py`'s shared chunk-JSON fixture helper,
`_make_chunk_json()`, to include a `fetched_at` key so every test in this file that drives
`RagIngester.ingest_url_group()` against a real on-disk fixture file keeps passing once
`ingester.py`'s `ingest_url_group()` reads `first_data["fetched_at"]` (mandatory key access)
instead of today's `first_data.get("fetched_at")`.

## Scope
- In scope: `tests/rag/ingestion/test_rag_ingester.py`'s `_make_chunk_json()` helper only
  (currently defined once, near the top of the file, with 10 call sites across
  `TestRagIngester`, `TestAtomicity`, and `TestCacheInvalidation`).
- Out of scope: `ingester.py`'s own migration (own implementation document, per this plan's
  Phase 2); `test_rag_ingester_callback.py` (own implementation document — see companion doc
  `20260823-200056_test_rag_ingester_callback.py.md`); `test_ingester.py` (own implementation
  document per this plan's Affected areas table).

## Assumptions
- Confirmed by reading the file: `_make_chunk_json()` builds a chunk JSON `dict` matching
  `ChunkSplitter`'s output shape. It currently has no `fetched_at` key at all (not even a
  `None`/empty placeholder) — the field is entirely absent from the returned dict.
- Confirmed via grep: all 10 call sites (`_make_chunk_json()` invoked with no arguments) rely
  entirely on the helper's defaults; none pass an explicit `fetched_at` today (the parameter
  does not exist yet), so a single default-value addition at the helper covers every call site
  uniformly.
- Confirmed by reading `ingester.py`: `ingest_url_group()` calls
  `self._read_chunk_json(chunk_files[0])` unconditionally as its first step, then reads
  `first_data.get("fetched_at")` (to become `first_data["fetched_at"]` per this plan's Phase 2).
  `_read_chunk_json()` delegates to `pipeline_utils._read_chunk_json_raw()`, which validates
  only `url`/`content` and returns the parsed dict otherwise unmodified — it does not validate
  `fetched_at` presence itself, so a dict missing the key reaches `first_data["fetched_at"]`
  unfiltered and raises `KeyError` once the plan's Phase 2 edit lands.
- Consequently, every test that calls `ingester.ingest_url_group(...)` directly against a
  `_make_chunk_json()`-derived file — `TestRagIngester.test_ingest_url_group_success`,
  `test_force_reinsert`, and `TestAtomicity.test_forced_reingest_with_embedding_failure`,
  `test_database_failure_during_replacement`, `test_partial_preparation_failure`,
  `test_successful_replacement` — reaches the `first_data["fetched_at"]` line regardless of
  whether `_prepare_chunks`/`_insert_chunks_batch` is mocked, because that access happens before
  either mocked method is invoked.
- `TestCacheInvalidation`'s three tests call `ingester.ingest_all()` with `_process_url_groups`
  mocked directly, so `ingest_url_group()`'s body (and its `first_data["fetched_at"]` access) is
  never reached for them; they route through `_group_chunks_by_url()` -> `_read_chunk_json()`
  only, which does not require `fetched_at`. These three tests are not at risk, but keeping the
  shared helper's output consistent everywhere is simpler than special-casing them.
- No test in this file asserts on `fetched_at`'s value today (confirmed by grep: no
  `fetched_at` reference anywhere in this file), so adding the key introduces no assertion
  conflict.

## Design decisions
- Add a `fetched_at: str = "2024-01-01T00:00:00Z"` parameter to `_make_chunk_json()` (canonical
  UTC form matching the plan's `YYYY-MM-DDTHH:MM:SSZ` convention) and include it in the returned
  dict, rather than editing all 10 call sites individually — a single default-value addition at
  the shared helper covers every call site uniformly, consistent with how this file already
  fixed an analogous gap for `chunk_type` in a prior implementation document.
- Place the new parameter and dict key next to the other envelope-level fields (near `etag`/
  `last_modified`) rather than at the end, so the fixture's shape mirrors the production
  `ChunkSplitter` output order the docstring says it matches.

## Alternatives considered
- Overriding `fetched_at="2024-01-01T00:00:00Z"` explicitly at each of the 10 call sites instead
  of adding a default — rejected: more edits for the same outcome, and defeats the helper's
  purpose of keeping call sites terse.
- Leaving this file unedited and relying on `ingester.py`'s migration alone — rejected: would
  make every real-call-path test in this file fail with `KeyError: 'fetched_at'` as soon as
  Phase 2 lands, which is exactly the gap this plan's Affected areas table calls out for this
  file.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`

### Procedure
1. In `_make_chunk_json()`'s signature, add a new keyword parameter
   `fetched_at: str = "2024-01-01T00:00:00Z"`.
2. In the `dict` literal `_make_chunk_json()` returns, add `"fetched_at": fetched_at,` alongside
   the existing `"etag"`/`"last_modified"` keys.
3. Leave all 10 call sites unmodified (none need an explicit override) — confirm by re-running
   the file's suite once `ingester.py`'s Phase 2 migration has landed.

### Method
- Single-parameter, single-key default-value addition to one shared helper; no test logic,
  assertion, or call-site change required.

### Details
- No test in this file constructs a chunk JSON missing a key to exercise fallback/error
  behavior — the fixture always represents a "complete, valid" chunk file, so adding the
  mandatory `fetched_at` key keeps that invariant rather than introducing a new missing-key
  test case (missing-key/malformed-`fetched_at` coverage belongs to `test_ingester.py`'s own
  implementation document per this plan's Phase 5 test list).
- `ChunkDocument` itself is never constructed directly in this file (confirmed by grep: no
  `ChunkDocument(` call site here) — this file only builds raw chunk JSON dicts consumed via
  the file-on-disk + `_read_chunk_json()` path, so the `models_data.py` dataclass-field-order
  change does not touch this file directly.

## Compatibility considerations
- N/A: test-fixture-only change; no production behavior is affected, and no other test file
  imports this file's `_make_chunk_json()` helper (confirmed by grep — it is module-private and
  unused outside this file).

## Security considerations
N/A: test-only file, no external input surface.

## Rollback considerations
- Trivial to revert (single default-value/key addition); no other file depends on this helper's
  exact shape.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` — all existing tests pass both
  before and after `ingester.py`'s Phase 2 migration lands, once this fixture update is applied.
- Cross-check: run this file's suite against the current (pre-migration) `ingester.py` too —
  `first_data.get("fetched_at")` accepts the added key exactly as it accepted its prior absence,
  so this fixture edit alone introduces no behavior change ahead of the migration.
- Per the plan's Validation plan table, also run
  `uv run pytest tests/rag/ingestion/test_ingester.py tests/rag/ingestion/test_rag_ingester.py tests/rag/ingestion/test_rag_ingester_callback.py -v`
  together once all Phase 1-4 source changes land, to confirm the INSERT-level `fetched_at`
  propagation assertions in `test_ingester.py` and this file's real-call-path tests are mutually
  consistent.

## Out of scope
- `ingester.py`'s own `first_data.get("fetched_at")` -> `first_data["fetched_at"]` migration and
  its `_insert_document()`/`_commit_url_transaction()` signature widening — own implementation
  document.
- `models_data.py`'s `ChunkDocument.fetched_at` field addition and `pipeline_utils.py`'s
  `read_json_file()` change — not exercised by this file (see Assumptions).
- New test coverage asserting the INSERT always includes the `fetched_at` column — that
  coverage belongs to `test_ingester.py` per the plan's Phase 5 list.

## Execution Status

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-095054_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-200056
- Related target files: tests/rag/ingestion/test_rag_ingester.py
