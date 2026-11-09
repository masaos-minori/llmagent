## Goal

- Reject an embedding BLOB whose length does not match the expected dimension inside `EmbeddingService.embed_and_store`, before any transaction, so the group takes the existing `failed/` routing (`REQ-001`: wrong-size embedding rejection).

## Scope
**Release unit**: N/A: not part of a release unit

- One method only: `EmbeddingService.embed_and_store` in `scripts/rag/ingestion/embedding.py`.

## Assumptions

- The failure reuses `IngestionFailureReason.VALIDATION_FAILED` (no new enum member), per the Plan's Assumptions; the human-readable size message reaches the failure log.
- The expected size is the module constant surface of `scripts/db/store_protocols.py` (`get_embedding_dims()` / `get_embedding_bytes()`, currently 1024 dims = 4096 bytes); a model change updates that constant, and the rejection follows it.

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

- `validate_embedding_blob` enforces the 1024-dim constant; existing `tests/rag/ingestion/test_ingester.py` stubs use `_DIM = 384` fake embeddings, so those fixtures must be aligned (see the seq-4 test procedure: derive the fake vector length from `get_embedding_dims()`).
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Confirm the tests added by the seq-4 document pass | Pending | — | — | Tests live in `tests/rag/ingestion/test_ingester.py` (own procedure document) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
