# Fix AttributeError and chunk loss in Japanese sentence merging

## Priority
High

## Summary
`ChunkJapaneseMixin._merge_ja_sentence_pairs` mixes a local `result` list with an
uninitialized instance list `self._result`. In production the multi-chunk Japanese path
raises `AttributeError` and crashes chunking; even if `_result` existed, emitted chunks
would be lost because the method returns the local list. Fix the state handling so all
emitted chunks are returned.

## Background
Introduced by commit 37f020f39 (2026-06-29, "refactor(chunk_japanese): extract buffer
management helpers"), which moved the intermediate `result.append(...)` calls into the
extracted helpers as `self._result.append(...)` while the final append and the tail-merge
check still use the local `result`. `_result` is only a bare class annotation; no
production code initializes it.
Verified by reproduction: calling `_merge_ja_sentence_pairs` with pairs that trigger
`_emit_and_start_new` raises `AttributeError: 'ChunkSplitter' object has no attribute
'_result'`, and `ChunkSplitter.process_file` crashes end to end on a 1049-character
Japanese document with the production config (`max_chunk = 500` in
`config/chunk_splitter.toml`). `ChunkSplitter.process_all` does not catch
`AttributeError`, so the whole chunk stage aborts.
The existing tests mask the defect in two places: `_make_ja_mixin` in
`tests/rag/ingestion/test_chunk_splitter.py` manually initializes `mixin._result` and
its tests call `_emit_and_start_new` directly, never through `_merge_ja_sentence_pairs`;
and `test_process_file_end_to_end_japanese` pre-initializes `chunker._result = []` before
calling `process_file`, with assertions (`result >= 1`, `len(outputs) == result`) weak
enough to pass while content is lost — re-verified: with that compensation a 1400-char
Japanese document under `max_chunk = 1000` writes 1 chunk (456 chars); without it the
same call raises `AttributeError`.

## Problem
Any Japanese document longer than `max_chunk` (500 chars by default) crashes
`ChunkSplitter` with `AttributeError`. The mixed local/instance lists also mean emitted
chunks would never reach the returned list if the crash were fixed by initialization
alone.

## Reason for Change
Every normal Japanese crawl document exceeds 500 chars, so the crash hits the normal
production path, not an edge case. Silent chunk loss (if only the crash is patched)
corrupts the RAG index.

## Implementation Intent
Restore a single source of truth for the chunk result inside
`_merge_ja_sentence_pairs`: either make the merge helpers operate on a caller-owned list
passed as a parameter (preferred: no cross-method instance state for chunk accumulation),
or initialize `self._result` at the start of `_merge_ja_sentence_pairs` and use it
consistently for emit, final append, tail merge, and the return value. Preserve the
public behavior of `_chunk_japanese`: same overlap semantics, same min/max chunk
constraints, same `normalized_content` handling (empty normalized maps to None).

## Target Files or Areas
- `scripts/rag/ingestion/chunk_japanese.py`
- `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- Eliminate the split between the local `result` and `self._result` in
  `_merge_ja_sentence_pairs` and its helpers (`_emit_and_start_new`,
  `_merge_tail_into_last`).
- Remove the test-fixture compensation (`mixin._result = []` in `_make_ja_mixin` and the
  `chunker._result = []` pre-initialization in `test_process_file_end_to_end_japanese`) so
  the production class is exercised as-is, and strengthen that test's assertions so
  emitted chunks cannot be silently lost.
- Add a regression test that drives `_merge_ja_sentence_pairs` (not just
  `_emit_and_start_new`) with enough sentences to trigger at least two emits plus a
  short-tail merge, asserting all emitted chunks are returned in order.

## Constraints
- Do not change chunking output semantics (overlap, min/max handling) beyond making the
  existing intended behavior actually work.
- Keep the mixin attribute-declaration pattern for type checkers; do not introduce a new
  abstraction.

## Acceptance Criteria
- A Japanese document longer than `max_chunk` chunks successfully via
  `ChunkSplitter.process_file` without `AttributeError` (covered by a test).
- `_merge_ja_sentence_pairs` returns every emitted chunk, including overlap-carrying
  emits and the merged short tail.
- `_make_ja_mixin` no longer pre-initializes internal state that production does not
  initialize.
- Full `tests/rag/ingestion` suite passes.

## Testing Expectations
- Unit regression test through `_merge_ja_sentence_pairs` with multi-emit input
  (overlap > 0 and overlap == 0 cases).
- One end-to-end `ChunkSplitter.process_file` test with Japanese text longer than
  `max_chunk`.
- `uv run pytest tests/rag/ingestion` and standard lint/type gates on touched files.

## Documentation Impact
No documentation change required unless a RAG chunking doc claims the Japanese
multi-chunk path behavior; re-check `docs/24_eventbus`-adjacent RAG docs only if they
describe Japanese chunking guarantees.

## Out of Scope
- English and Markdown chunking paths.
- Overlap length tuning or config changes.
- Sudachi tokenizer behavior.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether production has already ingested documents during the crash window (37f020f39
  onward) with partially written chunk output worth re-verifying in the live RAG DB.

## AI Implementation Instruction
Fix the state handling in `_merge_ja_sentence_pairs` with the minimal change; do not
rewrite the English mixin or the splitter I/O layer. Delete the `_result` fixture
compensation only after the production fix makes it unnecessary. Stop and report if the
intended tail-merge semantics for multi-emit input are ambiguous.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261106-073538
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`
