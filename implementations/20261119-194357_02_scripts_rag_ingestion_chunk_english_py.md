## Goal

Route the English accumulation path (`ChunkEnglishMixin._merge_paragraphs_en`) through the collaborator added in `chunk_utils.py` (`REQ-003`), dropping the mixin's own accumulation loop and overlap handling while keeping sentence splitting and the stopword-filtered `min_chunk` enforcement in the mixin. Output must be byte-identical to the current behavior (`REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The English oversized-item behavior (an overlong paragraph is split by `_split_sentences_en`, which keeps an overlong sentence whole) is intentional per-language behavior to preserve, not a defect (`Plan Assumptions`). It is expressed as the English oversized-item strategy input to the collaborator.
- `_chunk_english` still performs the stopword filtering and enforces `min_chunk` on the filtered length after the collaborator returns; the collaborator itself does not filter or apply `min_chunk` for English.
- `self._buf` remains valid until removed by `ragcrv006`; this row moves accumulation out of the instance but does not delete the field yet.

## Design decisions
- The collaborator receives the paragraph list, separator `"\n"`, `min_chunk`, `max_chunk`, `chunk_overlap`, the English oversized-item strategy (sentence-split-keep-whole), and the short-tail strategy (grow buffer mid-stream, append final buffer unconditionally). No design decision of its own is needed beyond selecting these strategy values.
- `_split_sentences_en` and `_filter_stopwords_en` stay in the mixin unchanged; only `_merge_paragraphs_en`'s loop body is replaced by a collaborator call.

## Alternatives considered
- Keeping `_flush_and_split`/`_flush_and_merge` as mixin helpers vs. folding them into the strategy inputs: folding preserves the single-loop invariant (`REQ-001`) and removes the second copy of the accumulation rule from the mixin.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_english.py`

### Procedure
1. Replace the body of `_merge_paragraphs_en` with a single call to the collaborator, passing paragraphs, `"\n"`, `self._min_chunk`, `self._max_chunk`, `self._chunk_overlap`, the English oversized-item strategy, and the English short-tail strategy.
2. Remove the now-dead `_flush_and_split` and `_flush_and_merge` helpers and the `self._buf` assignment (the field declaration stays until `ragcrv006`).
3. Keep `_split_sentences_en`, `_filter_stopwords_en`, and `_chunk_english` unchanged.

### Method
- Reproduce the current control flow exactly: skip empty paragraphs; split `len(para) > self._max_chunk` via sentence splitting (keeping an overlong sentence whole); grow the buffer while it fits; otherwise flush-and-merge with overlap; append the final buffer unconditionally. The collaborator expresses each branch as a strategy input so the observable chunk list is identical.

### Details
- The English short-tail end-of-stream behavior ("append the final buffer unconditionally") differs from code/Japanese; encode it as the English short-tail strategy value rather than erasing it.

## Compatibility considerations
- `_merge_paragraphs_en`'s signature and return type are unchanged; `_chunk_english` is unaffected.

## Security considerations
N/A: text accumulation only.

## Rollback considerations
N/A: revert the commit; the loop body restores the prior inline implementation.

## Validation plan
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` English cases produce zero diff from baseline.
- Characterization: the Phase 1 per-path fixture for English passes unchanged.

## Completion criteria
- `_merge_paragraphs_en` delegates to the single collaborator; English chunk output is byte-identical; `_chunk_english`'s stopword filtering and `min_chunk` enforcement are intact.

## Out of Scope
- The code path (`chunk_utils.py`/`chunk_splitter.py`) — covered by its own row.
- The Japanese paired-companion path — covered by its own row.
- Removing `self._buf` — sequenced to `ragcrv006`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route `_merge_paragraphs_en` through the collaborator | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (route English path, keep sentence splitting and filter-driven `min_chunk`) and `REQ-005`/`REQ-006` (behavior/output unchanged)
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-185003_ragcrv005_unify-chunk-merge-strategies.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-194357
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`
