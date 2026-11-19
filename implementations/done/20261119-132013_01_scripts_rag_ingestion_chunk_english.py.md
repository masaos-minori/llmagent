## Goal

Restore the invariant that an English chunk's stored `content` is the original
crawled text region (not a stopword-stripped projection), per `REQ-001`
(content equals the crawled region, no words removed) and `REQ-002`
(`normalized_content` is `NULL`, Shape B, filtering dropped).

## Scope
**Release unit**: english-content-stopword-loss

## Assumptions

- The `min_chunk` discard basis is `len()` over the post-filter (stopword-stripped)
  string, matching the current code at `chunk_english.py:30-31`. This Plan preserves
  that basis and only changes what is *stored*, not what is measured for discard.
- `_filter_stopwords_en` (`chunk_english.py:83`) is still called to compute the discard
  basis; only its stored value is dropped (Shape B).
- `_merge_paragraphs_en` (`chunk_english.py:34`) already returns the unfiltered merged
  paragraph regions; the current bug is that `_chunk_english` discards those and keeps
  only the filtered strings instead.

## Design decisions

- **Store unfiltered originals, drop the projection (Shape B).** `_chunk_english`
  returns the raw regions from `_merge_paragraphs_en`; `_filter_stopwords_en` is
  computed solely to preserve the existing `min_chunk` discard basis and is otherwise
  discarded. This restores INV-01 without amending INV-04.
- **Discard basis unchanged.** Keep `len(filtered_string) >= min_chunk`; do not switch
  to measuring the unfiltered length. This is the "same measurement basis the current
  code uses" required by `REQ-005`.

## Alternatives considered

- `N/A: Shape A (store the stopword-stripped projection as `content`) was rejected by
  the owner decision (UNK-01, 20261119-130500); ADR-009 INV-04 already dictates
  `NULL` for English, so Shape A would require amending INV-04 with no FTS
  measurement to justify it. This document implements Shape B only.`

## Implementation
### Target file
`scripts/rag/ingestion/chunk_english.py`

### Procedure
1. In `_chunk_english`, stop returning the `_filter_stopwords_en` results as the
   stored chunks. Return the **unfiltered** regions produced by
   `_merge_paragraphs_en` instead.
2. Preserve the discard basis: compute `_filter_stopwords_en(r)` for each raw region,
   and discard a region when `len(filtered) < self._min_chunk`. Keep the raw (unfiltered)
   region when it passes.
3. Update the `_chunk_english` docstring to state that it returns the unfiltered English
   text regions and that the `min_chunk` discard is measured on the post-filter length.

### Method
Replace the current tail of `_chunk_english` (`chunk_english.py:29-31`):

```python
paragraphs = re.split(r"\n{2,}", text.strip())
raw_chunks = self._merge_paragraphs_en(paragraphs)
filtered = (self._filter_stopwords_en(r) for r in raw_chunks)
return [c for c in filtered if len(c) >= self._min_chunk]
```

with a version that keeps the raw regions and uses the filtered length only for the
discard decision:

```python
paragraphs = re.split(r"\n{2,}", text.strip())
raw_chunks = self._merge_paragraphs_en(paragraphs)
# Discard basis preserved: measure len over the post-filter (stopword-stripped)
# string. Store the UNFILTERED original as content (Shape B, REQ-001/REQ-002).
filtered = [self._filter_stopwords_en(r) for r in raw_chunks]
return [raw for raw, stripped in zip(raw_chunks, filtered) if len(stripped) >= self._min_chunk]
```

`_filter_stopwords_en` is still invoked (to preserve the discard basis) but its result
is no longer stored. Then update the docstring on `_chunk_english`
(`chunk_english.py:27`) to remove the "discards chunks below min_chunk after
stopword removal" implication and state that it returns the unfiltered regions and that
the `min_chunk` discard is measured on the filtered-string length.

### Details

- Only `_chunk_english` changes. `_filter_stopwords_en` (`chunk_english.py:83`),
  `_merge_paragraphs_en` (`chunk_english.py:34`), `_split_sentences_en`, and imports
  (`re`, `chunk_utils.start_next_buf`) are untouched.
- No new symbols or imports are created.
- The Japanese path (`chunk_japanese.py`) and code path (`_chunk_code`) are not touched
  (`REQ-004`).

## Compatibility considerations

- `embedding.py:embed_and_store` computes `embedding = self.get_embedding(content)`
  (`embedding.py:91`) from `content`. Restoring the original `content` therefore changes
  every English embedding; existing production chunks must be re-chunked and re-embedded
  (manual deployment step, out of scope here, `REQ-003`).
- `chunks.normalized_content` stays `NULL` for English (Shape B), so FTS5's
  `COALESCE(normalized_content, content)` now indexes the original text. FTS results for
  English may change; see the FTS regression tests.

## Security considerations

`N/A: no auth, secrets, network, or user-data handling changes. `content` was already
written to the chunk JSON before this change; only its value changes.`

## Rollback considerations

Revert the single commit restoring `_chunk_english`.

## Validation plan

- Unit: run `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — the new test
  asserts `content` has no words removed and `normalized_content` is `NULL` for a
  non-empty `en_stopwords` config (`REQ-001`, `REQ-002`, `REQ-006`).
- Regression: `tests/rag/test_fts_fallback.py`, `tests/rag/test_fts_sync.py`,
  `TestChunkPayloadKeyContract`, and the Japanese chunking tests stay green.
- Coverage: `uv run diff-cover coverage.xml --compare-branch=master` >= 90% on changed
  lines.

## Completion criteria

- `_chunk_english` returns the unfiltered regions from `_merge_paragraphs_en`; the
  `min_chunk` discard is measured on the post-filter length.
- A non-empty `en_stopwords` config yields a chunk whose `content` equals the crawled
  region (whitespace-normalized) with every word present, and whose `normalized_content`
  is `NULL`.
- All listed tests pass; no Japanese-path or code-path test regresses.

## Out of Scope

- `normalized_content` emission (`chunk_splitter.py`, `REQ-002`) — covered by the sibling
  procedure for `chunk_splitter.py`.
- The REQ-006 test body itself — covered by the sibling procedure for
  `tests/rag/ingestion/test_chunk_splitter.py`.
- `docs/...` updates (`REQ-005`, `REQ-007`) — covered by the sibling docs procedures.
- Japanese normalization, code-block chunking, stopword-list / chunk-size constants.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-19 | 2026-11-19 | Returns UNFILTERED regions; discard basis on post-filter length (Shape B, REQ-001/REQ-002) |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-19 | 2026-11-19 | Regression test added by seq 03; snapshot baseline regenerated |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-19 | 2026-11-19 | ruff format+check + pytest; 62/62 incl new test; 822 RAG tests pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-19 | 2026-11-19 | Doc/ADR updates handled by sibling seq 04/05 |

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
- **Requirement ID**: `REQ-001` (restore original English `content`), `REQ-002`
  (`normalized_content` NULL, Shape B), `REQ-005` (`min_chunk` discard basis preserved)
- **Source issue**: `issues/20261119-112014_ragcrv002_english-content-stopword-loss.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-123746_ragcrv002_english-content-stopword-loss.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-132013
- **Related target files**: `scripts/rag/ingestion/chunk_english.py`
