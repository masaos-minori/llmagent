## Goal

Add a characterization test exercising Japanese chunking with `chunk_overlap > 0`
(REQ-002) to pin down pre-refactor behavior before `_emit_and_start_new()` is
refactored to use `start_next_buf()`, per `plans/20260826-120822_plan.md`.

## Scope

- In scope: one new test in `tests/rag/ingestion/test_chunk_splitter.py` exercising
  multi-chunk Japanese chunking with `chunk_overlap > 0`, plus a targeted case for
  the empty-buffer-at-overlap-start edge case identified during this Plan's own
  adversarial verification.
- Out of scope: any change to `scripts/rag/ingestion/chunk_japanese.py` itself
  (separate target file, seq 02, in this same pass — this item must land and pass
  against the *current, pre-refactor* code first); any English-chunking test.

## Assumptions

- This test must be authored and run against the **current** (pre-refactor)
  `_emit_and_start_new()` implementation first, to pin down its actual output —
  per this Plan's own Implementation steps Phase 1, and per `rules/ai-execution.md`'s
  general incrementalism principle (a pinning test must exist before refactoring
  untested behavior).
- `ChunkSplitter` (`chunk_splitter.py:62`) mixes in both `ChunkJapaneseMixin` and
  `ChunkEnglishMixin` — construct it directly (matching this test file's existing
  pattern) rather than instantiating `ChunkJapaneseMixin` alone, since
  `_chunk_overlap`/`_max_chunk`/`_min_chunk` are declared on the mixin but populated
  by `ChunkSplitter.__init__`.

## Design decisions

- Cover two cases in this item:
  1. The general case REQ-002 specifies: Japanese text long enough to produce
     multiple chunks with `chunk_overlap > 0`, asserting the overlap content
     carried into each subsequent chunk.
  2. The edge case found during this Plan's own adversarial verification
     (2026-08-27, see the Plan's Design "Edge-case note"): a scenario where
     `_orig_buf`/`_norm_buf` is empty at the moment `_emit_and_start_new()` is
     called with `chunk_overlap` truthy — `start_next_buf()` would return
     `next_item` unstripped in this case, while the current inline code always
     strips. Constructing this exact trigger requires reading
     `_merge_ja_sentence_pairs()`'s three-way branch (`_append_to_buffer` /
     `_emit_and_start_new` / `_reset_buffer`, lines 87-93) carefully — confirm
     whether this edge is actually reachable given the `_min_chunk`/`_max_chunk`
     guard conditions before asserting a specific expected output; if unreachable,
     document that finding in this test's docstring instead of asserting a
     synthetic case.
- Author the test to fail immediately if run against a deliberately-altered overlap
  slice (per this Plan's own Acceptance Criteria verification method for REQ-002) —
  do this as a manual authoring-time check, not a permanent part of the test suite.

## Alternatives considered

- Testing only via `chunk_utils.py`'s existing `start_next_buf()` unit tests
  (asserting the helper itself is correct) was considered and rejected — REQ-002
  specifically requires a Japanese-mixin-level characterization test, since the
  goal is confirming `_emit_and_start_new()`'s *integration* of the helper (via two
  parallel buffer calls) is behavior-preserving, not re-testing the helper in
  isolation.

## Implementation
### Target file
`tests/rag/ingestion/test_chunk_splitter.py`

### Procedure
1. Read `_merge_ja_sentence_pairs()`'s full branch logic (lines 77-101 of
   `chunk_japanese.py`) to determine realistic input sentence sequences that
   trigger `_emit_and_start_new()` at least twice (producing 3+ output chunks) with
   `chunk_overlap > 0`.
2. Add a new test constructing `ChunkSplitter` with a small `_max_chunk`/
   `_min_chunk`/`chunk_overlap` and Japanese input designed to hit that path,
   asserting the exact overlap content in the second/third chunk's `orig`/`norm`
   text.
3. Investigate whether the empty-buffer-at-overlap-start edge case (Design decisions
   above) is reachable; add a targeted case if so, or a documented negative finding
   if not.
4. Run this new test against current (pre-refactor) `chunk_japanese.py` and confirm
   it passes — this is the pinning step Phase 1 requires.
5. Manually verify the test would fail against a deliberately-altered overlap slice
   (e.g. temporarily change `[-self._chunk_overlap:]` to `[-self._chunk_overlap -
   1:]` in a scratch copy) to confirm the test is not vacuously passing, then revert
   the scratch change — do not commit this manual check.

### Method
Direct test-file addition (Edit tool) — one or two new test functions/methods in
this file's existing style; no changes to existing tests.

### Details
Follow this file's existing test-construction pattern (read a few existing tests in
this file for `ChunkSplitter` instantiation conventions — constructor arguments,
fixture usage — before writing the new test, to match established style rather than
introducing a new one).

Example shape (adjust exact API calls to match verified `ChunkSplitter` construction
conventions in this file):
```python
def test_japanese_chunking_with_overlap_produces_expected_overlap_content() -> None:
    splitter = ChunkSplitter(
        max_chunk=<small value>,
        min_chunk=<small value>,
        chunk_overlap=<N>,
        # ... other required constructor args, matching this file's existing
        # ChunkSplitter instantiation pattern
    )
    text = "<Japanese text designed to produce 3+ chunks>"
    chunks = splitter._chunk_japanese(text)  # or whatever the public entry point is
    assert len(chunks) >= 3
    # Assert the overlap tail of chunk[i] appears at the start of chunk[i+1]'s
    # orig/norm text, matching current (pre-refactor) _emit_and_start_new() output.
```
Confirm the actual public entry-point method name (`_chunk_japanese` per this
file's docstring conventions, or whatever `ChunkSplitter` exposes) by reading the
class before finalizing.

## Compatibility considerations

- Test-only change; no production code path is affected by this item alone.
- This test's expected values are derived from the CURRENT (pre-refactor) behavior
  — it must be authored and passing BEFORE seq 02 (`chunk_japanese.py`'s refactor)
  is applied, per this Plan's own Phase 1 ordering.

## Security considerations

- N/A: test-only change, no security-relevant code path.

## Rollback considerations

- New-test-only revert via `git diff`/`git checkout -- <path>`; independent of seq
  02 — this test can be reverted alone without affecting `chunk_japanese.py`.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/rag/ingestion/test_chunk_splitter.py` | Unit (new characterization test) | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py -v` | New test(s) pass against current (pre-refactor) `chunk_japanese.py` |

## Completion criteria

- A new test exercises Japanese chunking with `chunk_overlap > 0` across multiple
  output chunks and passes against current (pre-refactor) code.
- The empty-buffer-at-overlap-start edge case has been investigated and either
  covered by an assertion or documented as unreachable.
- The test has been manually confirmed to fail against a deliberately-altered
  overlap slice (proving it is not vacuous).

## Out of scope

- Any change to `scripts/rag/ingestion/chunk_japanese.py` (separate target file,
  seq 02, must land AFTER this item passes against current code).
- English-chunking tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read `_merge_ja_sentence_pairs()` branch logic to design trigger input | Pending | — | — | |
| 2 | Add the multi-chunk overlap characterization test | Pending | — | — | |
| 3 | Investigate and cover (or document as unreachable) the empty-buffer edge case | Pending | — | — | |
| 4 | Run test against current code, confirm it passes | Pending | — | — | |
| 5 | Manually confirm test fails against an altered overlap slice, then revert | Pending | — | — | |

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
- **Requirement ID**: REQ-002
- **Source issue**: `issues/20260821_07_issue.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260826-120822_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260827-112033
- **Related target files**: `tests/rag/ingestion/test_chunk_splitter.py`
