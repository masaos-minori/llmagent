# English chunk content stores stopword-stripped text

## Priority
High

## Summary
`ChunkEnglishMixin._chunk_english` returns stopword-filtered text as the chunk content, so English
`chunks.content` holds a lossy derivative of the crawled page and the original text is never stored.
`normalized_content` is `NULL` for English, so nothing preserves the original either.

## Background
- `_chunk_english` maps every merged chunk through `_filter_stopwords_en` and keeps only the filtered
  strings; `_build_text_triples` writes them as `("text", c, "")`, and `_build_chunk_payload` stores the
  empty normalized value as `NULL`.
- Reproduced at head `6bdced7bb`: source "The quick brown fox is a lazy animal that lives near the river
  bank today." is stored as `quick brown fox lazy animal that lives near river bank today.` with
  `normalized_content: null`.
- `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` INV-01 states `chunks.content` is the only text
  used for the LLM Context, INV-04 states English gets `normalized_content = NULL` falling back to
  `content`, and INV-06 states the original text is not restored from `normalized_content`. The ADR also
  records that chunk embeddings are computed from `content`.
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md` documents stopword removal only as the
  discard threshold ("chunks smaller than `min_chunk` after stopword removal are discarded"); it does not
  state that the stored text itself is filtered.
- No test asserts the filtering effect: every English chunk test in
  `tests/rag/ingestion/test_chunk_splitter.py` and `tests/rag/ingestion/test_rag_ingestion_pipeline.py`
  uses `en_stopwords: []`.

## Problem
The only text kept for English documents is a stopword-removed projection. The LLM context, the embedding,
and the FTS5 fallback all read that projection, and the crawled original cannot be recovered without a
re-crawl. This contradicts the text-separation invariants the Japanese path follows.

## Reason for Change
RAG output quality and index consistency depend on which text is authoritative. The behavior is currently
undocumented and untested, so it cannot be distinguished from a legacy defect.

## Implementation Intent
Restore the invariant that `content` is the crawled text and the normalized projection lives in
`normalized_content`, which is the column FTS5 already selects with `COALESCE`. Decide with the owner
whether English stopword filtering is kept as a normalized projection or removed entirely, then implement
one of those two shapes in the English chunker only.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_english.py` (`_chunk_english`, `_filter_stopwords_en`)
- `scripts/rag/ingestion/chunk_splitter.py` (`_build_text_triples`, `_build_chunk_payload`)
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
- `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` (only if the invariant wording must change)

## Required Changes
- Keep the unfiltered crawled text as the stored `content` for English chunks.
- If stopword filtering is kept, store its result in `normalized_content` so FTS5 indexes it and the
  original stays intact.
- Keep the `min_chunk` discard decision based on the same measurement basis the current code uses, and
  state that basis in the docs.
- Add the first test that asserts the stored English `content` and `normalized_content` values.

## Constraints
- ADR-009 INV-01, INV-02, INV-04, INV-06 must hold after the change; if the owner decides to keep the
  current shape, the ADR must state it explicitly instead of leaving the contradiction.
- Changing what `content` holds means existing English chunks must be regenerated with
  `chunk_splitter.py --force` and re-embedded; embeddings change, so search quality must be re-checked.
- Embeddings must keep being computed from `content`, per ADR-009.
- The Japanese path and its Sudachi normalization must not change.

## Acceptance Criteria
- For an English source, the written chunk `content` equals the crawled text region it came from
  (whitespace-normalized), with no words removed.
- `normalized_content` is either `NULL` (filtering dropped) or the stopword-removed projection
  (filtering kept), matching the decision recorded in the ADR.
- A new test asserts both fields for a non-empty `en_stopwords` configuration.
- FTS5 search behavior is re-verified by the existing FTS tests.

## Testing Expectations
- Unit: `_chunk_english` with a non-empty stopword list returns original text (or asserts the chosen
  shape explicitly).
- Unit: `_build_text_triples` maps the English projection to the correct payload field.
- Integration: existing `tests/rag/test_fts_fallback.py` and `tests/rag/test_fts_sync.py` stay green.
- Regression: `TestChunkPayloadKeyContract` stays green.
- Manual: re-chunk and re-embed one English source, then run the RAG consistency check.

## Documentation Impact
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`: state exactly what English `content` and
  `normalized_content` contain.
- `docs/21_rag/rag_05_01-configuration-reference.md`: state what `en_stopwords` actually affects.
- `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`: record the decision as an invariant or an
  explicit exception, with the tradeoff.

## Out of Scope
- Japanese normalization behavior.
- Code-block chunking.
- Chunk size tuning.

## Dependencies
- Owner decision on the intended English normalization shape (see Unresolved Questions).
- `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md` invariants are the contract this issue must align with.

## Unresolved Questions
- Whether stopword-stripping `content` is the intended design or a legacy shortcut — `Needs confirmation`
  from the owner; no rationale was found in the docs.
- Whether production English chunks must be regenerated in the same release as the fix.
- Whether stopword filtering improves FTS5 search quality measurably; no measurement exists.

## AI Implementation Instruction
Do not implement both shapes. Confirm the owner's decision first, then change only the English path.
Do not adjust stopword lists or chunk-size constants as part of this issue.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-002`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112014
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_splitter.py`, `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`, `docs/10_adr/adr_02_06_009_rag-fts5-text-separation.md`
