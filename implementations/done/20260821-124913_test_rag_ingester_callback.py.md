## Goal
Ensure `tests/rag/ingestion/test_rag_ingester_callback.py`'s single test keeps passing once
`read_chunk_json()` raises `ChunkFormatError` instead of returning `None` on an unparseable
chunk file, resolving whether `ingester.py`'s `_group_chunks_by_url()` call site must
catch-and-convert that exception.

## Scope
- In scope: `tests/rag/ingestion/test_rag_ingester_callback.py` only (94 lines, 1 test
  function: `test_ingest_all_calls_on_ingest_complete`, line 81).
- Out of scope: `ingester.py`'s own migration (own implementation document) — this document
  identifies a dependency on a decision made there, but does not make that decision.

## Assumptions
- Confirmed by reading the file: there is no literal chunk/crawl JSON dict anywhere in this
  file. The "fixture" is a bare `MagicMock()` standing in for a chunk-file `Path`
  (`mock_chunk_dir.glob.return_value = [MagicMock()]`, lines 85-91), with `_process_url_groups`
  mocked to return `[]`.
- `ingest_all()` (`ingester.py:124-138`) calls `self._group_chunks_by_url(chunk_files)`
  (line 138) BEFORE `_process_url_groups` — the one thing this test mocks. `_group_chunks_by_url()`
  (`ingester.py:694-719`) calls `self._read_chunk_json(path)` for every glob result, including
  the `MagicMock()` stand-in.
- **Gap found (adversarial review, 2026-08-21), added to `plans/20260820-094150_plan.md`'s
  Affected-areas table:** today, `MagicMock().read_bytes()` returns another `MagicMock`, and
  `orjson.loads(<MagicMock>)` raises `orjson.JSONDecodeError` — caught by the current
  `_read_chunk_json_raw()` (`pipeline_utils.py:49-53`), which returns `None`. `_group_chunks_by_url()`
  silently skips this "file" on `None`, and the test passes only because of this graceful
  skip.
- Once `read_chunk_json()` is specified (per the plan's own Assumptions) to raise
  `ChunkFormatError` on every validation failure rather than return `None`, whether this test
  continues to pass depends entirely on whether `ingester.py`'s `_read_chunk_json()` wrapper
  (`ingester.py:552-554`) is changed to catch `ChunkFormatError` and convert it back to `None`
  at the `_group_chunks_by_url()` call site — this is undecided by the current plan text and
  must be resolved during `ingester.py`'s Phase 2 implementation, not assumed here.

## Design decisions
- This document does not prescribe which of the two outcomes `ingester.py`'s implementation
  should choose (catch-and-skip vs. let-it-raise) — that is `ingester.py`'s design decision
  (see its own implementation document, which already flags that each of the 6
  `_read_chunk_json()` call sites' `if data is None` guard becomes either a
  `try/except ChunkFormatError` guard or a propagating raise, "decide per-call-site during
  implementation, preserving each method's existing skip-and-log-and-continue vs.
  skip-and-return-failure behavior").
- For THIS test file: if `ingester.py`'s implementation preserves the current
  skip-unparseable-file behavior (catch-and-skip), no edit is needed here — the test's
  `MagicMock()` fixture continues to be silently skipped, and the test's assertion (that
  `on_ingest_complete` callback fires with the mocked `_process_url_groups` result) is
  unaffected.
- If `ingester.py`'s implementation instead lets `ChunkFormatError` propagate out of
  `_group_chunks_by_url()`, this test's `ingest_all()` call will raise instead of completing,
  and the test must be rewritten to either (a) supply a `MagicMock()` that produces valid JSON
  bytes via `read_bytes.return_value = orjson.dumps({...full valid chunk payload...})` instead
  of an unparseable mock, or (b) wrap the `ingest_all()` call in `pytest.raises(ChunkFormatError)`
  if raising-on-unparseable is the intended new behavior for this code path specifically.

## Alternatives considered
- Preemptively rewriting this test now to supply a fully-valid mock JSON payload, regardless
  of `ingester.py`'s eventual behavior — rejected: this would mask which of the two outcomes
  `ingester.py`'s implementation actually produces (a valid-payload mock passes either way,
  hiding a regression if the "let it raise" path was in fact chosen unintentionally). Better to
  keep the test's current shape as a live probe of `ingester.py`'s error-handling contract,
  and adjust only after that contract is confirmed.

## Implementation
### Target file
`tests/rag/ingestion/test_rag_ingester_callback.py`

### Procedure
1. After `ingester.py`'s migration lands, run this file's test unedited first (see Validation
   plan) to observe which of the two outcomes actually occurred.
2. If it passes unedited: no code change needed in this file; done.
3. If it raises `ChunkFormatError` (or any other exception) out of `ingest_all()`: apply one of
   the two fixes described in Design decisions above, matching whichever behavior
   `ingester.py`'s implementation document ultimately specifies for
   `_group_chunks_by_url()`'s unparseable-file handling.

### Method
- Do not modify this file speculatively before observing the actual post-migration behavior —
  the whole point of this fixture is that it currently depends on a specific error-handling
  path that the migration may or may not preserve.

### Details
- If a rewrite is needed (step 3), the minimal fix is: replace
  `mock_chunk_dir.glob.return_value = [MagicMock()]` with a mock whose `read_bytes()` returns
  `orjson.dumps({<full valid chunk payload — see test_rag_ingester.py's `_make_chunk_json()`
  helper for the complete mandatory-key shape>})`, so the file "successfully" parses as an
  empty-but-valid group (or adjust the assertion to expect the group to appear in
  `_process_url_groups`'s input, if that's now observable).

## Compatibility considerations
- This test is the one place in the plan's scope where a genuine behavior-preservation
  question (not just a fixture-shape question) is unresolved. Flag it explicitly in the PR/
  commit description for `ingester.py`'s migration so a reviewer understands why this test's
  outcome is a signal, not noise.

## Security considerations
N/A — test-only file, no external input surface.

## Rollback considerations
- Low risk either way — single test, no other file depends on this one's fixture shape.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_rag_ingester_callback.py -v` after `ingester.py`'s
  migration lands — observe pass/fail, then apply the Implementation Procedure above based on
  the outcome.

## Out of scope
- Deciding `ingester.py`'s own error-handling contract for `_group_chunks_by_url()` — that
  belongs to `ingester.py`'s own implementation document.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260820-094150_plan.md
- Source implementation procedure: N/A
- Generated at: 20260821-124913
- Related target files: test_rag_ingester_callback.py
