# Japanese sentence-merge drops short leading sentences before oversized ones

## Priority
Medium

## Summary
`ChunkJapaneseMixin._merge_ja_sentence_pairs` discards a short sentence when it precedes a
sentence too large to fit in the running buffer, whereas the English path
(`merge_text_items`) tail-merges short items instead of dropping them. A Japanese document
that contains a short sentence (< `min_chunk`) immediately before a very long sentence loses
the short sentence's original text entirely on every ingestion run. Make the Japanese merge
retain the short sentence (merge it into the next chunk or emit it alone) so no source text
is silently dropped.

## Background
`ChunkSplitter` composes `ChunkEnglishMixin` and `ChunkJapaneseMixin` via multiple inheritance.
Both text paths accumulate sentences into buffers bounded by `min_chunk`/`max_chunk`
(`config/chunk_splitter.toml`: `min_chunk=40`, `max_chunk=500`, `chunk_overlap=50`). The English
accumulator lives in `scripts/rag/ingestion/chunk_utils.py::merge_text_items`, whose contract
(docstring + behavior) is "A short tail item is merged into the last chunk instead of discarded."
The Japanese accumulator lives in
`scripts/rag/ingestion/chunk_japanese.py::_merge_ja_sentence_pairs`. Both sit in the same
unvalidated sizing area flagged by `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md`.

## Problem
- `_merge_ja_sentence_pairs` (`scripts/rag/ingestion/chunk_japanese.py`) branches on each
  `(orig, norm)` pair: if `len(buf) + len(orig) + 1 <= max_chunk` it appends; else if
  `len(buf) >= min_chunk` it emits and starts a new buffer; **else it resets the buffer to
  `orig`**, discarding whatever was already accumulated.
- When the running buffer holds a short sentence shorter than `min_chunk` and the next sentence
  does not fit, the third branch fires and the accumulated short sentence is dropped, never
  emitted.
- Reproduced at HEAD with config bounds (min=40, max=500): a 30-char lead sentence followed by a
  480-char sentence yields one 480-char chunk; the 30-char lead is absent from the output.
- The English equivalent (`merge_text_items`) never drops: it merges the short item into the
  next chunk, producing one larger chunk instead of losing data. The asymmetry is a Japanese-only
  correctness defect.

## Reason for Change
Ingestion must not silently drop source text. For Japanese corpora, any document containing a
short clause before a long one is at risk, and the loss is silent (the run reports success and
the total chunk count). The fix aligns the Japanese path with the documented English contract
("merge, do not discard") and removes an untested assumption that every accumulated sentence is
retained.

## Implementation Intent
In `_merge_ja_sentence_pairs`, replace the buffer-reset branch so a short sentence that cannot
join the oversized next sentence is retained rather than dropped. Prefer emitting the short
sentence as its own chunk (even if below `min_chunk`) or appending it to the next chunk's front,
whichever keeps behavior deterministic and preserves all original text. Do NOT change the English
`merge_text_items` algorithm or the text chunkers' `max_chunk` behavior. Preserve overlap handling
and the `None`-normalized COALESCE semantics.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_japanese.py` (`_merge_ja_sentence_pairs`)
- `tests/rag/ingestion/test_chunk_splitter.py` (Japanese mixin is exercised here)
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` (if merge-vs-emit policy changes)

## Required Changes
- Ensure every non-empty original sentence in a Japanese document appears in at least one emitted
  chunk; no source text is dropped by the merge step.
- Add a unit test (in `test_chunk_splitter.py`, where the Japanese mixin is exercised) asserting
  a short sentence (< `min_chunk`) preceding an oversized sentence is retained, not dropped.
- Add a regression test covering the exact reproduced case (30-char lead + 480-char sentence over
  budget).
- If the doc's merge policy table distinguishes English vs Japanese, note the retention rule.

## Constraints
- Do not change `merge_text_items` or the English/Japanese text chunkers' `max_chunk` behavior.
- Preserve `chunk_overlap` behavior and the `None` normalized-form COALESCE fallback.
- Code chunking (`_chunk_code`) is out of scope for this issue.
- Retained chunks may fall below `min_chunk`; that is acceptable and preferable to data loss.

## Acceptance Criteria
- No original Japanese sentence is dropped by `_merge_ja_sentence_pairs`.
- The reproduced short-lead + oversized-sentence case retains the lead sentence in output.
- Existing Japanese/English splitter tests pass unchanged.

## Testing Expectations
- Unit: `_merge_ja_sentence_pairs` with a short lead before an oversized sentence retains the lead.
- Regression: the exact reproduced case (min=40, max=500) keeps the 30-char lead.
- Run `uv run pytest tests/rag/ingestion` and confirm no regression.

## Documentation Impact
If the merge policy is documented in `rag_02_03_ingestion_pipeline-chunksplitter.md`, note that
the Japanese path retains short sentences (never drops them), matching the English contract
(intent and boundary only; no implementation-derived detail per `skills/DESIGN.md` docs policy).

## Out of Scope
- Changing the English `merge_text_items` algorithm or its tail-merge behavior.
- Changing `min_chunk`/`max_chunk`/`chunk_overlap` values (tracked separately, see `nc034`).
- The code-chunk size bound (tracked separately, see `ragc001`).

## Dependencies
- `issues/done/20260927-211412_nc034_confirm-rationale-for-chunk-size-bounds.md` — same unvalidated
  sizing area. Depends on: nc034 closure (value choice) is independent of the retention fix, which
  is correct regardless of the specific bounds.

## Unresolved Questions
- Owner preference: emit the short sentence as its own sub-`min_chunk` chunk, or prepend it to the
  next chunk? Both retain data; prefer the simpler deterministic option.
- Does retaining sub-`min_chunk` chunks change downstream embedding/index expectations? Confirm the
  pipeline accepts small chunks.

## AI Implementation Instruction
Only edit `_merge_ja_sentence_pairs` in `scripts/rag/ingestion/chunk_japanese.py`. Replace the
buffer-reset branch so a short sentence that cannot join an oversized next sentence is retained
(emitted alone or prepended), never dropped. Do not touch `merge_text_items` or the English
chunker. Add a unit + regression test pinning the retained-lead case. Keep the diff to
`chunk_japanese.py` and its tests. Stop and report if retaining sub-`min_chunk` chunks breaks a
downstream test.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-060510
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
