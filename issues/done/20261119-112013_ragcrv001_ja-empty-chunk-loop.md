# Japanese chunking emits an empty chunk that breaks the completion sentinel

## Priority
High

## Summary
`ChunkJapaneseMixin._merge_ja_sentence_pairs` emits an empty chunk pair when the first sentence of a
document is longer than `max_chunk`. The empty chunk is written as `{stem}-0000.json`, the file the
pipeline uses as its completeness sentinel, so the ingester always quarantines it and the source is
re-chunked on every subsequent run.

## Background
- `ChunkSplitter.process_file` treats `{stem}-0000.json` as the sentinel (`pipeline_utils.is_already_processed`)
  and `ChunkSplitter.publish_chunk_files` publishes it last, so its presence is the only completeness signal.
- The buffer-retain branch in `_merge_ja_sentence_pairs` (added by `issues/done/20261107-060510_ragc002_ja-sentence-merge-content-loss.md`)
  appends the current buffer unconditionally before starting a new one. When the buffer is still empty
  (first sentence oversized) the appended pair is `("", None)`.
- Reproduced at head `6bdced7bb` with `max_chunk=500`, `min_chunk=40` and a 700-character Japanese sentence:
  3 chunk files written, `ja-0000.json` has empty `content`, `read_chunk_json` raises
  `ChunkFormatError: chunk: missing or invalid 'content'`, `ChunkGroupingStrategy.group` rejects it as
  `parse_failed`, `FileRouter.route` moves it to `failed/`, the sentinel is gone, and the next
  `process_file(force=False)` writes the same 3 chunks again.
- Existing regression test `TestJapaneseMergeRetention.test_short_lead_before_oversized_is_retained`
  covers only the non-empty short-buffer case; the empty-buffer case is uncovered.
- Related closed work: `issues/done/20261107-055949_ragc001_code-chunk-size.md`,
  `issues/done/20261118-025816_chunkov001_split-overlong-nonpositive-maxchunk.md`,
  `issues/done/20261106-073538_raging001_japanese-chunk-merge-crash.md`.

## Problem
An oversized first Japanese sentence produces a chunk whose content is empty. That file can never be
ingested, consumes `chunk_index` 0, becomes the sentinel, and produces a repeating
chunk → quarantine → re-chunk cycle that re-embeds the valid chunks of the same document on every run.

## Reason for Change
The loop is silent (only an INFO "chunked N chunks" line and one WARNING per run) and repeats embedding
cost for every affected document. It is a residual gap of the already closed ragc002 fix, not a new design.

## Implementation Intent
Make the Japanese merger satisfy the same oversized-item contract the shared helper already implements:
an item longer than `max_chunk` is segmented (the strategy `chunk_utils._split_overlong` applies in
`merge_text_items`), and no chunk is ever emitted from an empty buffer. Keep the sentence-splitting
responsibility in the Japanese chunker and the segmentation rule in the shared helper so the two paths
cannot drift again.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_japanese.py` (`_merge_ja_sentence_pairs`, `_split_into_ja_sentences`)
- `scripts/rag/ingestion/chunk_utils.py` (shared oversized-item rule)
- `tests/rag/ingestion/test_chunk_splitter.py`

## Required Changes
- Emit a chunk only when the buffer holds non-empty text.
- Segment an oversized Japanese sentence so no emitted pair exceeds `max_chunk` without an explicit,
  documented exception.
- Ensure the emitted `chunk_index` series for one document is contiguous from 0 and that index 0 always
  carries real content.
- Keep `normalized_content = None` semantics for sentences whose normalization yields nothing.

## Constraints
- Must not regress `TestJapaneseMergeRetention`: a short sentence that cannot join an oversized next
  sentence stays retained.
- Preserve the atomic publish order (`publish_chunk_files` publishes `-0000` last) and the temp-file
  cleanup contract from `issues/done/20261108-131236_ragrev017_partial-chunk-write-gap.md`.
- `content` must never be empty in any written chunk file (`read_chunk_json` treats it as invalid).
- No behavior change to the English, code, or Markdown-heading paths in this issue.

## Acceptance Criteria
- A document whose first Japanese sentence exceeds `max_chunk` produces zero empty chunk files.
- Every emitted Japanese chunk satisfies `len(content) <= max_chunk`, or the exception is documented in
  `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`.
- After one ingestion pass, `{stem}-0000.json` is no longer present in `chunk/` and a following
  `process_file(force=False)` returns 0 with a "skip (already chunked)" log line.
- Existing chunk tests stay green.

## Testing Expectations
- Unit: `_merge_ja_sentence_pairs` with a single oversized first sentence emits no empty pair and no
  oversized pair (regression test for this issue).
- Unit: parameterized oversized-first-sentence cases for `min_chunk < max_chunk` and `min_chunk` close to
  `max_chunk`.
- Integration: `ChunkSplitter.process_file` plus `ChunkGroupingStrategy.group` plus `FileRouter.route`
  for a Japanese document with an oversized first sentence — assert nothing lands in `failed/` and the
  sentinel is consumable.
- Regression: `TestJapaneseMergeRetention`, `TestJapaneseChunkOverlap`, `TestAtomicChunkWrite` stay green.

## Documentation Impact
`docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`: state the Japanese path's oversized-sentence
rule and that a written chunk file always carries non-empty content. No ADR change expected; if the
emission rule changes materially, note it in the ADR-009 Implementation Notes.

## Out of Scope
- Unifying the three merge implementations (issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md).
- Configuration validation (issues/20261119-112015_ragcrv003_chunk-config-validation.md).
- English `content` stopword behavior (issues/20261119-112014_ragcrv002_english-content-stopword-loss.md).
- Re-tuning `min_chunk`, `max_chunk`, `chunk_overlap` values.

## Dependencies
- `issues/done/20261107-060510_ragc002_ja-sentence-merge-content-loss.md` (introduced the buffer-retain branch).
- Sibling: issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md is the structural follow-up that removes the duplicated merger.

## Unresolved Questions
- Whether any production source in `/opt/llm/rag-src` actually contains a Japanese sentence longer than
  `max_chunk` with no `。！？` or newline boundary — `Needs confirmation` from the corpus or `chunk.log`.
- Whether segmentation at character level is acceptable for Japanese text quality, or the sentence must
  be split at Sudachi clause boundaries instead — needs owner decision before implementation.

## AI Implementation Instruction
Do not special-case the empty buffer with a filter in the writer; fix the emission rule in the merger.
Do not change the English or code paths. Add the regression test before the fix and keep it in the commit.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-001`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112013
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `scripts/rag/ingestion/chunk_utils.py`, `tests/rag/ingestion/test_chunk_splitter.py`
