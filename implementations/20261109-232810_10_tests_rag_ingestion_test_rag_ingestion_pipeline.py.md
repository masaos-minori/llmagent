## Goal

- Keep the crawler → chunk splitter → ingester end-to-end suite aligned with the fixed embedding dimension, so the pipeline tests stop asserting on a fake vector length the production validator now rejects (`REQ-001`).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- `tests/rag/ingestion/test_rag_ingestion_pipeline.py` only.

## Assumptions

- Measured at HEAD `02f3143e2` in a scratch worktree: the embedding-size check alone makes 4 tests in this file fail; the `chunk_type` domain check alone makes none fail here, because the payload builder already defaults to a valid value (`chunk_type: str = "text"`, current L125).
- Failing names (measured): `TestChunkSplitterOutputEndToEnd::test_real_chunk_splitter_output_is_ingested`, `TestJsonLifecycle::test_full_pipeline_preserves_metadata`, `TestReingest::test_sha256_different_content_triggers_reingest`, `TestReingest::test_sha256_etag_changes_triggers_reingest`.
- This file's own `chunks` table fixture declares `chunk_type TEXT` with no `CHECK` constraint (current L51), so the failures are embedding-length only, not schema-driven.

## Design decisions

- Derive the fake embedding length from `get_embedding_dims()` in `scripts/db/store_protocols.py` instead of writing the literal `1024`: the same source the new validator reads, so a future dimension change updates both sides at once.
- Change the stubs, not the assertions: the four tests verify lifecycle and reingest behavior, and their current failure is a fixture that no longer satisfies the production validator.

## Alternatives considered

- Bypassing the new size check in these tests with a narrower patch target (patching `embed_and_store` instead of `get_embedding`): rejected — it would hide the end-to-end path the suite exists to cover.

## Implementation
### Target file
- `tests/rag/ingestion/test_rag_ingestion_pipeline.py`

### Procedure
- Replace every fixed-length fake embedding with a length derived from the production dimension constant.

### Method
- Add `from db.store_protocols import get_embedding_dims` to the test module's import block.
- Replace all five occurrences of `return_value=[0.1] * 128` (current L245, L288, L365, L421, L446) with `return_value=[0.1] * get_embedding_dims()`.
- Update the stale comment in `test_removed_code_blocks_rejected` (current L428-431): after the seq-7 change the unparseable file DOES carry a generic `.error.json` sidecar; the comment's "carries no .error.json" claim is corrected (no assertion change — the test asserts rejection + non-persistence only).
- Leave the payload builder (`_chunk_payload`, current L118-146) unchanged: its `chunk_type` default is already in the schema domain.

### Details
- The stubs patch `EmbeddingService.get_embedding` (`patch.object(EmbeddingService, "get_embedding", ...)`), which is upstream of the new size check in `embed_and_store` (`scripts/rag/ingestion/embedding.py`), so the returned list length is what the validator measures after `floats_to_blob`.
- `[0.1] * 128` produces a 512-byte BLOB, which the validator rejects with `Embedding BLOB must be 4096 bytes (1024 float32 dims), got 512`; that rejection is what made the four tests fail.

## Compatibility considerations

- Fixture-only change; no assertion changes and no coverage removed.

## Security considerations
N/A: test data only.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_rag_ingestion_pipeline.py -q` — the 4 measured failures are green once the seq-1 change lands; each stays green on HEAD only after the stub length is corrected together with the production change (on HEAD the longer vector is simply accepted).
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- The 4 measured failing tests pass with the pipeline running the real size validation (AC-1 end to end).

## Out of Scope

- Production validation logic (seq-1, seq-2 documents).
- The `chunks` table fixture's missing `CHECK (chunk_type ...)` constraint: adding it here would duplicate the schema tests and is not required by this plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261110-120906 | Test-only procedure: no production change end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 2 | Add or update tests per Validation plan | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261110-120924 | N/A: not in scope |

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
- **Requirement ID**: `REQ-001` (reject wrong-size embeddings before the transaction)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `tests/rag/ingestion/test_rag_ingestion_pipeline.py`