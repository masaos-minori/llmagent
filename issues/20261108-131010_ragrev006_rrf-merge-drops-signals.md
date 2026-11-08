# RRF merge keeps only the last list entry and reports a misleading distance or BM25 score

## Priority
Medium

## Summary
`RagScorer.rrf_merge` stores `meta[cid] = item` for every list, so a chunk found by both the vector leg and the FTS leg ends up with the signal of whichever list was processed last and the default `0.0` for the other.

## Background
Review finding F-008. Evidence (Explicit in code, Verified by reproduction): merging `[[vector hit distance=0.1], [fts hit bm25=-3.0]]` for the same `chunk_id` returned `distance 0.0, bm25_score -3.0`; reversing the list order returned `distance 0.1, bm25_score 0.0`. `0.0` is a valid "perfect match" distance, so the dropped value is indistinguishable from a real one. `MergedHit` values are copied into `RankedHit` and into diagnostics.

## Problem
Merged hits misreport their retrieval signals depending on list order, which makes diagnostics and any score-based tuning unreliable.

## Reason for Change
The merged hit is the record downstream diagnostics and rerank prompts rely on; silently losing one signal is an incorrect result even though the fused rank itself is unaffected.

## Implementation Intent
Combine the per-list signals into the merged hit (keep the distance from the vector list and the BM25 score from the FTS list) and represent "absent" explicitly instead of a numeric default.

## Target Files or Areas
- `scripts/rag/repository.py` (`RagScorer.rrf_merge`, `_dedup_hits`)
- `scripts/rag/models_data.py`, `shared.types` (`RawHit`, `MergedHit`)
- `tests/rag/` repository and fusion tests

## Required Changes
- Merge fields across lists for the same `chunk_id`.
- Use an explicit absent marker (or `None`) for a signal the chunk did not have, and handle it in consumers.
- Add an order-independence test.

## Constraints
- Do not change the RRF score formula or the ranking order.
- Keep the `MergedHit` constructor compatible for existing callers.

## Acceptance Criteria
- Merging the same chunk from the vector and FTS lists keeps both signals regardless of list order.
- The fused score and order are unchanged.

## Testing Expectations
- Unit tests for `rrf_merge` with both orders and with a chunk present in only one list.
- mypy for the changed dataclass fields.

## Documentation Impact
No documentation change expected.

## Out of Scope
- Tuning `rrf_k` or the fusion strategy.

## Dependencies
N/A: none

## Unresolved Questions
Whether any consumer reads `distance` or `bm25_score` from merged hits for a decision (not only for diagnostics) is `Needs confirmation`.

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131010
- **Related target files**: `scripts/rag/repository.py`, `scripts/rag/models_data.py`,`, `tests/rag/`
