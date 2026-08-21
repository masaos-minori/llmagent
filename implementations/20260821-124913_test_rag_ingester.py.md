## Goal
Update `tests/rag/ingestion/test_rag_ingester.py`'s shared chunk-JSON fixture helper so its
`chunk_type`/`source_file` defaults satisfy the new per-field value validation
(`chunk_type in {"text","code"}`) enforced by `read_chunk_json()`.

## Scope
- In scope: `tests/rag/ingestion/test_rag_ingester.py` only (430 lines, 9 test functions).
- Out of scope: `ingester.py`'s own migration (own implementation document); the
  `test_rag_ingester_callback.py`/`test_rag_ingestion_pipeline.py` files (own implementation
  documents).

## Assumptions
- Confirmed by reading the file: a single helper, `_make_chunk_json()` (lines 23-53), builds
  every fixture used across all 9 tests. It already includes all 15 mandatory keys (envelope
  `schema_version`/`artifact_type`/`created_by` + `url`/`title`/`lang`/`content`/`code_blocks`/
  `etag`/`last_modified`/`chunking_strategy`/`normalized_content`/`chunk_index`/`source_file`/
  `chunk_type`) — no key is missing, and `etag`/`last_modified`/`normalized_content` are
  correctly nullable.
- **Gap found (adversarial review, 2026-08-21), added to `plans/20260820-094150_plan.md`'s
  Affected-areas table:** `_make_chunk_json()` defaults `chunk_type=""` and `source_file=""`.
  The plan's own Design section specifies `chunk_type in {"text","code"}` value validation at
  the `read_chunk_json()` boundary. `""` is a valid `str` but not a member of `{"text","code"}`,
  so under that design every call site using the unmodified default will be rejected by
  `ChunkFormatError` once `ingester.py` is migrated — even though the key is present (this is a
  *value* rejection, not a *missing-key* rejection).
- All 10 call sites of `_make_chunk_json()` use the unmodified `chunk_type=""`/`source_file=""`
  default: lines 135, 168, 206, 240, 279, 281, 315, 351, 382, 410. None override these two
  parameters.
- `chunk_index=0` (default, int, non-negative, non-bool) already satisfies the new
  non-defaulted-but-present-and-valid requirement — no change needed for that field.
- Confirmed via `rg`: this file never calls `DocumentStore.chunk_insert()`/
  `SQLiteDocumentStore.chunk_insert()` — chunk writes go through `RagIngester`'s own raw-SQL
  `_insert_chunk()`/`_insert_chunks_batch()` path (`ingester.py:493-542`), a separate default
  pair unrelated to this plan's Phase 3 (`store_protocols.py`/`store_impl.py`).
- `ingest_url_group()` (`ingester.py:203`) calls `self._read_chunk_json(chunk_files[0])`
  unconditionally, even in tests that mock `_prepare_chunks` — so `test_ingest_url_group_success`
  and `test_force_reinsert` exercise the real (migrated) reader on the on-disk fixture file
  even though other internals are mocked. `test_forced_reingest_with_embedding_failure` does
  not mock `_prepare_chunks` at all, so its `_read_chunk_json` call at `ingester.py:698` also
  runs for real. The three `TestCacheInvalidation` tests mock `_process_url_groups` entirely,
  so their dummy chunk file's JSON is never actually parsed by the strict reader — those three
  need no fixture-value change to keep passing (their fixture becomes dead weight, not an
  active failure risk), but keeping the helper consistent everywhere is still the simplest fix.

## Design decisions
- Change `_make_chunk_json()`'s default parameter values for `chunk_type` from `""` to
  `"text"` (a valid enum member; matches this codebase's likely most-common case for markdown/
  plain-text chunks) rather than editing all 10 call sites individually — a single default-value
  change at the helper covers every call site uniformly, since none of the 10 call sites
  override this parameter today.
- Leave `source_file` at `""` unless the new schema also value-validates it (the plan's Design
  section lists an enum constraint only for `chunk_type`/`chunking_strategy`, not
  `source_file` — re-verify against the finalized `read_chunk_json()` implementation at
  implementation time; if `source_file=""` turns out to be rejected too — e.g. by a
  non-empty-string rule — give it a placeholder value such as `"test.json"` instead).

## Alternatives considered
- Overriding `chunk_type="text"` explicitly at each of the 10 call sites instead of changing
  the default — rejected: more edits for the same outcome, and the helper's whole purpose is
  to keep call sites terse; changing the default is the minimal, DRY fix consistent with the
  helper's existing design.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester.py`

### Procedure
1. In `_make_chunk_json()` (line ~30, the `chunk_type: str = ""` parameter default), change the
   default to `chunk_type: str = "text"`.
2. Re-verify `source_file`'s validation rule against the finalized `read_chunk_json()`
   implementation; if it is also value-constrained (not just presence-constrained), give its
   default a valid placeholder value in the same edit.
3. Run the full file's test suite (see Validation plan) to confirm all 9 tests still pass with
   the updated default — no test asserts on `chunk_type`'s specific value today (verified by
   grep: no `assert.*chunk_type` in this file), so this change should not alter any assertion
   outcome.

### Method
- Single-parameter default-value edit; no test logic, no assertion, no call-site change
  required.

### Details
- No test in this file constructs a JSON *missing* a key to test default-fallback behavior
  (all 15 keys are always present in `_make_chunk_json()`'s output) — the risk here is purely
  value-level (`chunk_type=""`), not key-presence, so this document's scope is narrower than a
  full fixture rewrite.

## Compatibility considerations
- None — this is a test-fixture-only change; no production behavior is affected.

## Security considerations
N/A — test-only file, no external input surface.

## Rollback considerations
- Trivial to revert (single default-value change); no other file depends on this helper's
  exact default.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -v` — all 9 tests pass after
  `ingester.py`'s migration lands and this default is updated.
- Cross-check: run this file's suite BEFORE `ingester.py`'s migration lands too (with the
  updated default) — the current (pre-migration) `ingester.py` code should still accept
  `chunk_type="text"` exactly as it accepted `chunk_type=""`, since it has no enum validation
  yet; this confirms the fixture edit alone doesn't regress against the current code.

## Out of scope
- `ingester.py`'s own reader migration and `_insert_chunk()`/`_insert_chunks_batch()` behavior.
- `store_protocols.py`/`store_impl.py`'s `chunk_insert()` default removal — this file never
  calls that method.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-124913
- Related target files: test_rag_ingester.py
