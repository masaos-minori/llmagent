## Goal

Route the Japanese accumulation path (`ChunkJapaneseMixin._merge_ja_sentence_pairs`) through the collaborator added in `chunk_utils.py` (`REQ-004`), modeling the paired (original, normalized) companion stream as a first-class collaborator input instead of a parallel buffer, while keeping morphological normalization. Output — including `None` normalized values — must be byte-identical to the current behavior (`REQ-005`, `REQ-006`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The paired (original, normalized) stream is preserved as part of the collaborator contract: each item carries a companion value plus a merge/overlap handler applied to both buffers (`Plan Implementation Intent`).
- `_split_overlong` (segment overlong sentence within `max_chunk`) and `start_next_buf` (overlap on both buffers) remain the primitives the collaborator composes.
- `None` normalized values are preserved and surfaced so downstream COALESCE falls back to the original text; the collaborator must carry the companion through `None` boundaries without collapsing them.
- `self._orig_buf`/`self._norm_buf` remain valid until removed by `ragcrv006`; this row moves accumulation out of the instance but does not delete the fields yet.

## Design decisions
- The collaborator accepts, per item, the primary value and an optional companion value plus a per-item merge/overlap function. For Japanese these are `(orig, norm)` and a handler that overlaps both buffers via `start_next_buf`; for code/English the companion is absent.
- The Japanese short-tail strategy (emit a `< min_chunk` buffer as its own chunk mid-stream, then start fresh; merge the final tail into the last pair) and the "empty buffer never emits" rule are encoded as the Japanese short-tail strategy input.

## Alternatives considered
- Passing two parallel lists (originals + normalizeds) vs. a single paired stream: the paired stream matches the current `list[tuple[str, str | None]]` shape and avoids index-alignment bugs; chosen.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_japanese.py`

### Procedure
1. Replace the body of `_merge_ja_sentence_pairs` with a single call to the collaborator, passing the pair list, separator `" "`, `self._min_chunk`, `self._max_chunk`, `self._chunk_overlap`, the Japanese oversized-item strategy (`_split_overlong`), the Japanese short-tail strategy, and a per-item companion handler that overlaps both buffers.
2. Remove the now-dead `_append_to_buffer`, `_emit_and_start_new`, `_reset_buffer`, `_merge_tail_into_last` helpers whose logic the collaborator now owns.
3. Keep `_split_into_ja_sentences`, `_normalize_ja_sentence`, and `_chunk_japanese` unchanged.

### Method
- Reproduce the current control flow exactly: segment `len(orig) > self._max_chunk` via `_split_overlong` (flushing any buffered lead first, dumping pieces without tail-merging); grow the buffer while it fits; emit-and-start-new with overlap when the buffer reaches `min_chunk`; emit a short buffer as its own chunk mid-stream; never emit an empty final buffer; merge a short final tail into the last pair. Apply overlap to both original and normalized buffers via `start_next_buf`. Preserve `None` normalized values throughout.

### Details
- Ensure the collaborator's companion handling keeps `(orig, self._norm_buf or None)` semantics, including the "empty buffer never emits" (`ragcrv001`) and "retain short buffer, don't drop" (`ragc002`) rules already verified in the current code.

## Compatibility considerations
- `_merge_ja_sentence_pairs`' signature and return type (`list[tuple[str, str | None]]`) are unchanged; `_chunk_japanese` is unaffected.

## Security considerations
N/A: text accumulation only.

## Rollback considerations
N/A: revert the commit; the loop body restores the prior inline implementation.

## Validation plan
- Regression: `uv run pytest tests/rag/ingestion/test_chunk_splitter.py` Japanese cases produce zero diff from baseline, including `None` normalized values.
- Characterization: the Phase 1 per-path fixture for Japanese (exact pair list incl. `None`) passes unchanged.

## Completion criteria
- `_merge_ja_sentence_pairs` delegates to the single collaborator with the paired companion stream as a contract input; Japanese pair output is byte-identical (incl. `None`); morphological normalization is intact.

## Out of Scope
- The code path and English path — covered by their own rows.
- Removing `_orig_buf`/`_norm_buf` — sequenced to `ragcrv006`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Route `_merge_ja_sentence_pairs` through the collaborator with paired companion input | Pending | — | — | |
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
- **Requirement ID**: `REQ-004` (route Japanese path preserving paired companion stream) and `REQ-005`/`REQ-006` (behavior/output unchanged)
- **Source issue**: `issues/20261119-112017_ragcrv005_unify-chunk-merge-strategies.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261119-185003_ragcrv005_unify-chunk-merge-strategies.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261119-194357
- **Related target files**: `scripts/rag/ingestion/chunk_japanese.py`
