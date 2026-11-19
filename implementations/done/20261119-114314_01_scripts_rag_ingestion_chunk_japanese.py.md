## Goal

Stop `ChunkJapaneseMixin._merge_ja_sentence_pairs` from emitting an empty chunk when the first Japanese sentence of a document exceeds `max_chunk`, and segment any oversized sentence so no emitted pair exceeds `max_chunk`. Implements `REQ-001` (no empty emission), `REQ-002` (oversized segmentation), `REQ-003` (contiguous index 0 with real content), and `REQ-004` (`normalized_content = None` preserved).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Oversized originals are split at character level via the shared `chunk_utils._split_overlong` (raw slicing), matching the Plan's intent to reuse the shared rule and keep it language-independent.
- Split sub-parts carry `normalized_content = None` so downstream COALESCE falls back to the original text; Sudachi normalization is not recomputed per sub-part.
- `chunk_index` contiguity and the last-`-0000` publish order are preserved by the existing `ChunkSplitter.publish_chunk_files` / `process_file` machinery and need no change here.
- `max_chunk > 0` is guaranteed by config validation (out of scope of this Plan); `_split_overlong` raises `ValueError` on `max_chunk <= 0`, consistent with the English path.
- UNK-01 (whether production corpus actually contains such a sentence) does not block the defensive fix.

## Design decisions
- **Direct segment-and-emit (English-path pattern).** In the `else` branch of `_merge_ja_sentence_pairs` (reached when a sentence does not fit the current buffer), first emit any retained short lead and reset the buffer, then if `len(orig) > self._max_chunk` dump the pieces from `_split_overlong(orig, " ", self._max_chunk)` directly into `result` as `(piece, None)` tuples and leave the buffer empty. This mirrors `chunk_utils.merge_text_items`, which segments an oversized item and resets the buffer, so the remainder is never tail-merged back into the previous chunk (which would exceed `max_chunk`) and each piece stays within `max_chunk`.
- **Empty-buffer / retention guard.** Emit the retained buffer only when `self._orig_buf` is non-empty; this is the defensive `REQ-001` guard and also satisfies the ragc002 retention requirement (a short lead before an oversized sentence is emitted, not dropped).

## Alternatives considered
- Emitting the oversized sentence whole and letting `ChunkGroupingStrategy.group` quarantine it: rejected — reproduces the sentinel/quarantine loop this Plan removes.
- Japanese-specific clause-boundary splitting via Sudachi: rejected — the Plan reuses the shared character-level helper so the JA and English/heading paths cannot drift again (UNK-02).

## Implementation
### Target file
`scripts/rag/ingestion/chunk_japanese.py`

### Procedure
1. Modify `_merge_ja_sentence_pairs` to pre-split oversized originals and guard the retain-branch emission.
2. Add the companion regression test (see Companion test files).

### Method
In `_merge_ja_sentence_pairs`, in the `else` branch: emit the retained short buffer when non-empty (resetting it), then if the sentence exceeds `max_chunk` extend `result` with `(piece, None)` for each `_split_overlong` piece; otherwise seed the buffer from the sentence.

### Details
- Import is already present: `from rag.ingestion.chunk_utils import start_next_buf`; add `_split_overlong` to that import.
- The empty-buffer case that currently emits `("", None)` is reached when the first sentence is oversized and `min_chunk > 0`; segmenting and dumping pieces directly removes that trigger, and the `if self._orig_buf:` guard removes it defensively for any residual empty buffer.
- Pieces are dumped directly (not fed through the buffer logic) so the last piece is not tail-merged into the previous chunk; each piece is `<= max_chunk`. (Feeding pieces through the buffer logic was rejected after a regression test showed the tail-merge produced a chunk exceeding `max_chunk` and `_emit_and_start_new` surfaced an empty-string normalized value for split parts.)
- `normalized_content` for split parts is `None` (`REQ-004`), surfaced as `(piece, None)`; COALESCE falls back to the original text.
- Retention behavior for the non-empty short-buffer case is preserved: the retained lead is emitted before the oversized sentence, so `TestJapaneseMergeRetention.test_short_lead_before_oversized_is_retained` still passes.

## Compatibility considerations
- No change to the English (`merge_text_items`), code-block, or Markdown-heading chunk paths — they use the shared helper directly and are unaffected.
- `_split_overlong` is called with the same `sep=" "` and `max_chunk` the English path uses; behavior is identical for the split itself.

## Security considerations
N/A: no input-sanitization, auth, or data-handling change.

## Rollback considerations
N/A: revert the commit that implements this procedure.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/chunk_japanese.py` | Unit | `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` | New regression test passes; all existing JA merge tests green |
| `scripts/rag/ingestion/chunk_japanese.py` | Lint/format | `uv run ruff format --check scripts/rag/ingestion/chunk_japanese.py` && `uv run ruff check scripts/rag/ingestion/chunk_japanese.py` | Clean |

## Completion criteria
- A single oversized first sentence (`len > max_chunk`) yields no empty pair and no pair longer than `max_chunk`.
- `TestJapaneseMergeRetention.test_short_lead_before_oversized_is_retained` still passes (no source text dropped).
- Every emitted JA chunk satisfies `len(content) <= max_chunk`; `normalized_content` is `None` for split sub-parts.
- `ruff format --check` and `ruff check` pass on the modified file.

## Out of Scope
- Unifying the three merge implementations (`issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`).
- Config validation of `min_chunk`/`max_chunk`/`chunk_overlap`.
- Changing the English, code-block, or Markdown-heading paths.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement oversized segmentation and empty-buffer guard in `_merge_ja_sentence_pairs` | Completed | 20261119-121446 | 20261119-121446 | REQ-001, REQ-002, REQ-003, REQ-004 |
| 2 | Add/update companion regression test | Completed | 20261119-121446 | 20261119-121446 | `tests/rag/ingestion/test_chunk_splitter.py` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261119-121446 | 20261119-121446 | ruff + pytest |

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
- **Requirement ID**: REQ-001 (no empty emission), REQ-002 (oversized segmentation), REQ-003 (index 0 has content), REQ-004 (`normalized_content = None`)
- **Source issue**: `issues/20261119-112013_ragcrv001_ja-empty-chunk-loop.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-113354_ragcrv001_ja-empty-chunk-loop.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-114314
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`, `tests/rag/ingestion/test_chunk_splitter.py`

### Companion test files
- `tests/rag/ingestion/test_chunk_splitter.py`
  - Procedure: add a regression test asserting a single oversized first sentence emits no empty pair and no oversized pair; add parameterized oversized-first-sentence cases for `min_chunk < max_chunk` and `min_chunk` close to `max_chunk`.
  - Validation: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` — new and existing tests green.