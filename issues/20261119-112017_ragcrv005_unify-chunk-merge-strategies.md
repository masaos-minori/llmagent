# Three chunk merge implementations implement the same rule differently

## Priority
Medium

## Summary
Chunk accumulation exists three times: `chunk_utils.merge_text_items`, `ChunkEnglishMixin._merge_paragraphs_en`
with `_split_sentences_en`, and `ChunkJapaneseMixin._merge_ja_sentence_pairs` with its own helpers. Each
implements min/max/overlap accumulation with different oversized-item and short-tail rules, which is the
structural cause of the divergent behavior in the chunking paths.

## Background
- `chunk_utils.merge_text_items` splits an overlong item with `_split_overlong`, merges a short tail into
  the last chunk, and applies overlap through `start_next_buf`. Used only by `ChunkSplitter._chunk_code`.
- `ChunkEnglishMixin._merge_paragraphs_en` sends an overlong paragraph to `_split_sentences_en`, which
  keeps an overlong sentence whole ("Oversized sentences are kept as-is"), merges a short tail through
  `_flush_and_merge` with overlap, and discards the final short buffer only through the caller's filter.
- `ChunkJapaneseMixin._merge_ja_sentence_pairs` never splits an overlong sentence, emits a short buffer as
  its own chunk, merges a short tail through `_merge_tail_into_last`, and applies overlap through
  `start_next_buf`. The missing oversized branch is what produces the empty chunk in
  issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md.
- Reproduced size divergence at head `6bdced7bb` with `max_chunk=100`: the code path never exceeds 100,
  the English path produces 226-character chunks, and the Japanese path produces a chunk equal to the
  whole oversized sentence plus an empty chunk.
- Closed related work: `issues/done/20261107-055949_ragc001_code-chunk-size.md` and
  `issues/done/20261107-060510_ragc002_ja-sentence-merge-content-loss.md` each patched one copy of the rule.

## Problem
One documented rule ("min/max bound chunk size, overlap prepends the previous tail") is implemented three
times with three outcomes. Every future change to chunking must be applied in three places, and each past
fix produced a partial behavior.

## Reason for Change
The chunkers are the core of the ingestion corpus quality and are actively tuned. Duplicated accumulation
logic is where the next divergence will appear.

## Implementation Intent
Extract one accumulation collaborator that owns min/max/overlap accumulation and takes the
language-specific decisions as explicit inputs: separator, oversized-item strategy, short-tail strategy,
and an optional paired-normalized companion stream. The chunkers keep their language-specific splitting and
normalization and stop owning buffer state.

## Target Files or Areas
- `scripts/rag/ingestion/chunk_utils.py`
- `scripts/rag/ingestion/chunk_english.py`
- `scripts/rag/ingestion/chunk_japanese.py`
- `scripts/rag/ingestion/chunk_splitter.py`
- `tests/rag/ingestion/test_chunk_utils.py`

## Required Changes
- Define one accumulator with the shared loop and explicit strategy inputs for oversized items and short tails.
- Route the English, Japanese, and code paths through that accumulator.
- Keep the normalized-companion pairing that the Japanese path needs as part of the accumulator contract
  instead of a parallel buffer.
- Keep `start_next_buf` and `_split_overlong` as the overlap and segmentation primitives behind it.
- Remove the per-mixin buffer fields once no path needs them (see issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md).

## Constraints
- Must be executed with the `python-refactoring` skill: characterization tests for all three current
  behaviors before extraction, and behavior-locked comparison of output before and after.
- No intended behavior change except the explicit, separately filed fixes (issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md,
  issues/20261119-112014_ragcrv002_english-content-stopword-loss.md). Any behavior the characterization tests reveal as a defect must be reported, not
  silently fixed here.
- The public chunk file output format and `chunk_index` ordering must not change.

## Acceptance Criteria
- Exactly one accumulation loop exists under `scripts/rag/ingestion/`.
- Characterization tests pin each path's current output before the extraction and pass unchanged after it.
- No mixin or class holds mutable chunk-buffer state.

## Testing Expectations
- Characterization: fixture documents per path asserting the exact chunk list before the change.
- Mutation-sensitive unit tests for the accumulator's oversized, short-tail, and overlap branches.
- Regression: `tests/rag/ingestion/test_chunk_utils.py`, `test_chunk_splitter.py`, `test_ingester.py`,
  `test_rag_ingestion_pipeline.py` stay green.

## Documentation Impact
`docs/21_rag/rag_02_07_ingestion_pipeline-utils.md`: describe the accumulator's ownership and the
strategy inputs each path supplies. Coordinate with issues/20261119-112022_ragcrv010_chunking-docs-max-chunk.md so the two doc updates do not
describe two different designs.

## Out of Scope
- Changing which text is stored for English (issues/20261119-112014_ragcrv002_english-content-stopword-loss.md).
- Fixing the empty-chunk defect (issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md) — file that first so its fix is a deliberate,
  visible behavior change rather than a side effect of the extraction.
- Configuration validation (issues/20261119-112015_ragcrv003_chunk-config-validation.md).

## Dependencies
- Depends on: issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md (behavior fix landed first).
- Related: issues/20261119-112018_ragcrv006_chunk-mixin-state-coupling.md (removes the mixin state the accumulator makes unnecessary).

## Unresolved Questions
- Whether the three paths should end up with one shared oversized-item strategy or keep per-language
  strategies — needs an owner decision on Japanese segmentation quality.

## AI Implementation Instruction
Write the characterization tests before touching any merger. Do not merge the three behaviors into
whichever one looks correct; report the differences instead. Keep the extraction inside the
`rag.ingestion` layer.

## Traceability
- **Workflow phase**: `python-code-review` (finding `F-005`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-112017
- **Related target files**: `scripts/rag/ingestion/chunk_utils.py`, `scripts/rag/ingestion/chunk_english.py`, `scripts/rag/ingestion/chunk_japanese.py`, `scripts/rag/ingestion/chunk_splitter.py`, `tests/rag/ingestion/test_chunk_utils.py`
