# Validate embedding data with one contract across ingestion and verification

## Priority
Medium

## Summary
Enforce the embedding dimension and element types at the provider-response boundary, and verify every stored vector with one reusable helper in consistency checks and recovery verification.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` M-01):
- Refuted in part: NaN and Infinity are already rejected before serialization. `floats_to_blob` runs `_validate_float_list` with `math.isfinite` and a float32 range check (`scripts/rag/utils.py:160-175`), and the embed response check rejects non-finite values (`scripts/rag/llm_client.py:297-309`). The note's claim that they reach persistence is not supported.
- Confirmed in part: both checks accept `bool` because `isinstance(True, int | float)` is true, and the response check enforces only a non-empty list, not 1,024 elements (`llm_client.py:298-300`).
- Confirmed: `_check_embedding_dimension` reads one row with `LIMIT 1` (`scripts/db/rag_consistency_queries.py:242-253`); the expected dimension constant is `QWEN3_EMBEDDING_DIMS = 1024` (`scripts/db/store_protocols.py:24`).
- Not verified: how `scripts/db/recovery_verification.py` validates vectors beyond reusing the consistency report.

## Problem
A wrong-length or boolean-containing embedding can pass the response check, and a single-row dimension check cannot show that the whole vector table is consistent.

## Reason for Change
One bad vector row breaks nearest-neighbor search silently; validation should be defined once and reused.

## Implementation Intent
One helper that validates length, element type (rejecting booleans), and finiteness, used by the embed response path, `floats_to_blob`, consistency checks (all rows via SQL), and recovery verification, with mismatch counts and a bounded sample of `chunk_id` values in safe diagnostics.

## Target Files or Areas
- `scripts/rag/llm_client.py`, `scripts/rag/utils.py`, `scripts/rag/ingestion/embedding.py`
- `scripts/db/store_protocols.py`, `scripts/db/rag_consistency.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/recovery_verification.py`
- `tests/rag/ingestion/`, `tests/db/`

## Required Changes
- Require exactly the configured number of elements and reject booleans, strings, and null in the response and before serialization (NaN and Infinity checks stay).
- Check all stored BLOB lengths in SQL; treat zero bytes, non-multiples of four, and unexpected lengths as mismatches.
- Report mismatch count and a bounded `chunk_id` sample with expected and observed dimensions; distinguish confirmed mismatch from inability to verify.
- Reuse the helper in ingestion, RAG consistency, and recovery verification.

## Constraints
- Diagnostics must not dump vector contents.
- The expected dimension stays defined in one place.

## Acceptance Criteria
- Invalid API responses are classified as validation failures; a bad vector after a valid first row is detected.
- Recovery verification rejects a database containing invalid vectors.
- Diagnostics identify count and sample rows without vector contents.

## Testing Expectations
Unit tests for each rejection class and a stored-table test with a malformed row after a valid one; whole-suite run and changed-path gates.

## Documentation Impact
Document the embedding validation contract in the RAG database and ingestion documents.

## Out of Scope
- Changing the embedding model or dimension.

## Dependencies
- Depends on issues/20261125-093148_ragrem003_rag-consistency-structured-probes.md (typed verification results) and issues/20261125-093151_ragrem006_rag-artifact-generations.md (artifact contract).

## Unresolved Questions
- `不明`: whether the embedding service always returns 1,024 elements for the selected model (the service response schema was not available).

## AI Implementation Instruction
Keep the existing finite and range checks; add the missing checks through one helper; do not change the dimension constant.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093154
- **Related target files**: `scripts/rag/llm_client.py`, `scripts/rag/utils.py`, `scripts/db/rag_consistency_queries.py`, `scripts/db/recovery_verification.py`
