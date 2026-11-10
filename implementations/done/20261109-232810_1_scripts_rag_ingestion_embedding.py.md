## Goal

- Reject an embedding BLOB whose length does not match the expected dimension inside `EmbeddingService.embed_and_store`, before any transaction, so the group takes the existing `failed/` routing (`REQ-001`: wrong-size embedding rejection).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- One method only: `EmbeddingService.embed_and_store` in `scripts/rag/ingestion/embedding.py`.

## Assumptions

- The failure reuses `IngestionFailureReason.VALIDATION_FAILED` (no new enum member), per the Plan's Assumptions; the human-readable size message reaches the failure log.
- The expected size is the module constant surface of `scripts/db/store_protocols.py` (`get_embedding_dims()` / `get_embedding_bytes()`, currently 1024 dims = 4096 bytes); a model change updates that constant, and the rejection follows it.
- Verified anchor set at HEAD `02f3143e2` (`git log -1 --oneline -- scripts/rag/ingestion/embedding.py` = `3d2dc8790`): `embed_and_store` signature at L71-73, `chunk_type: str = data.chunk_type or ""` at L85, `embedding = self.get_embedding(content)` at L89, the `embedding is None` warn-and-return block at L90-103, `return PreparedChunk(` at L104, `embedding_blob=floats_to_blob(embedding),` at L109.
- Verified choke point: `ChunkFactory._embed_and_store` (`scripts/rag/ingestion/chunk_preparation.py` L76-80) is a one-line delegation to `EmbeddingService.embed_and_store`, so no change is needed there and every embedded chunk passes the new check.
- Measured blast radius at HEAD `02f3143e2` in a scratch worktree: the size check alone fails 22 tests in `tests/rag/ingestion` (16 in `test_ingester.py`, 4 in `test_rag_ingestion_pipeline.py`, 2 in `test_ingester_index_generation.py`), and the full suite (12123 tests, 0 failures at HEAD) shows no failure outside `tests/rag/ingestion`.

## Design decisions

- Validate in `embed_and_store` right after `floats_to_blob`, the single choke point for every embedded chunk (reached through `ChunkFactory.prepare`).
- On mismatch, return `IngestionFailureReason.VALIDATION_FAILED` from `embed_and_store` (matching its existing `PreparedChunk | IngestionFailureReason` return contract) rather than raising, so the deterministic failure flows through the existing `ChunkFactory.prepare` → `failed_paths` routing with no new exception path.
- Import `validate_embedding_blob` from `db.store_protocols`: the `rag.ingestion` package already imports `db.*` submodules directly (`document_manager.py` imports `db.helper`), so no new contract edge.

## Alternatives considered

- Validate only at `chunks_vec` insert (`store_impl.py` already calls `validate_embedding_blob`): rejected — it raises inside the transaction as `OperationalError` from `vec0`, indistinguishable from transient lock/IO errors (Plan Background); this is the reason for the early check.
- A new `EMBEDDING_DIMENSION_MISMATCH` enum member: rejected by the Plan Design as unnecessary surface.

## Implementation
### Target file
- `scripts/rag/ingestion/embedding.py`

### Procedure
- Add the `validate_embedding_blob` import.
- In `embed_and_store`, build the BLOB once, validate it, and return `IngestionFailureReason.VALIDATION_FAILED` on a size mismatch with a warning log carrying the sizes.

### Method
- Add `from db.store_protocols import validate_embedding_blob` to the import block.
- After the `embedding is None` check (current L90-103), replace the inline `floats_to_blob(embedding)` call at L109:
  - `embedding_blob = floats_to_blob(embedding)`
  - `try:` `validate_embedding_blob(embedding_blob)` `except ValueError as e:` log a warning with `path.name` and `e` (the message names expected and actual bytes), `extra={"doc_id": doc_id, "url": data.url, "source_type": "file", "stage_name": "ingester"}`, then `return IngestionFailureReason.VALIDATION_FAILED`.
  - Pass `embedding_blob` to `PreparedChunk`.

### Details
- `get_embedding` is untouched: the length check is in `embed_and_store`, so the retry policy is unchanged (`REQ-005`).
- A returned `VALIDATION_FAILED` lands in `ChunkFactory.prepare`'s `failed_paths`; `ingest_url_group`'s gate at L329 skips `commit` entirely and routes the group to `failed/` (AC-1: no commit call).
- Only `ValueError` is caught: `validate_embedding_blob`'s `TypeError` cannot occur because `floats_to_blob` always returns `bytes`.

## Compatibility considerations

- `validate_embedding_blob` enforces the 1024-dim constant; the fake embeddings in `tests/rag/ingestion` are shorter and must be aligned by the test procedures in the same batch: `tests/rag/ingestion/test_ingester.py` `_DIM = 384` (L61-62) per the seq-4 document, 5 stubs in `tests/rag/ingestion/test_rag_ingestion_pipeline.py` per the seq-10 document, and 4 stubs in `tests/rag/ingestion/test_ingester_index_generation.py` per the seq-11 document.
- `floats_to_blob` (`scripts/rag/utils.py` L125) validates element type, emptiness, and finiteness but not length, so the size check has to be explicit; it is not already covered by the conversion helper.
- Correct-size payloads are byte-identical to today; `store_impl.py`'s own `validate_embedding_blob` calls stay as defense-in-depth.

## Security considerations
N/A: size validation on an internal BLOB; no new input surface.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_ingester.py -q` — the wrong-size test added by the seq-4 document fails on HEAD and passes after.
- `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- A stub embedding of the wrong length makes `embed_and_store` return `IngestionFailureReason.VALIDATION_FAILED`, the group ends in `failed/` with that reason, no `commit` runs, and the ingestion suites are green (AC-1).

## Out of Scope

- `get_embedding` retry behavior, new enum members, `chunk_type` validation (seq-2 document), commit-time routing (seq-3 document), documentation (seq-6 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-113819 | 20261110-113819 |  |
| 2 | Confirm the tests added by the seq-4 document pass | Completed | — | 20261110-114823 | Tests live in `tests/rag/ingestion/test_ingester.py` (own procedure document) seq-4 tests green: test_ingester.py 44 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261110-120906 | end-of-unit gate: tests/rag/ingestion 337 passed; full suite 12133 passed; diff-cover 100%; ruff/mypy/lint-imports pass |

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
- **Related target files**: `scripts/rag/ingestion/embedding.py`