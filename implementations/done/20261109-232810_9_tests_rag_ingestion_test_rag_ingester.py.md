## Goal

- Keep the `RagIngester` end-to-end suite aligned with the strict `chunk_type` domain, and add one case that pins the new `chunk_type` rejection routing (`REQ-002`).

## Scope
**Release unit**: ragrev015-core (Plan `### Release units`; owner-declared batch unit 20261110)

- `tests/rag/ingestion/test_rag_ingester.py` only.

## Assumptions

- Measured at HEAD `02f3143e2` in a scratch worktree: the `read_chunk_json` `chunk_type` domain check alone makes 5 tests in this file fail; the embedding-size check alone makes none fail here.
- Failing names (measured): `TestAtomicity::test_database_failure_during_replacement`, `TestAtomicity::test_successful_replacement`, `TestRagIngester::test_force_reinsert`, `TestRagIngester::test_ingest_url_group_success` (one is parametrized, hence 5 failures over 4 names).
- All measured failures come from one fixture default, not from `RagIngester` logic.

## Design decisions

- Fix the payload builder, not the assertions: `_make_chunk()` (current L36-62) defaults `chunk_type: str = ""` (current L41), which the strict rule rejects at read time, so every group built by these tests is rejected before `RagIngester` runs.
- Leave the `_group_key()` helper (current L83-95, `chunk_type=""` at current L94) unchanged: verified by probe that it stays green. It constructs `ChunkGeneration` values that are passed as the already-grouped input to `_process_url_groups` (current usage sites L418-419, L462-464), so its `chunk_type` never participates in grouping or in the read-time domain check.
- Add the new routing case at the `RagIngester` level, because the domain rejection itself is covered by the seq-5 document and what must be pinned here is where the rejected file ends up.

## Alternatives considered

- Changing `_group_key()` to `"text"` for cosmetic consistency: rejected as unnecessary churn — measured behavior does not depend on it, and the helper documents a value-object input, not a payload.

## Implementation
### Target file
- `tests/rag/ingestion/test_rag_ingester.py`

### Procedure
- Align the chunk payload default with the schema domain, then add one rejection-routing case.

### Method
- In `_make_chunk()`, change the default at current L41 from `chunk_type: str = ""` to `chunk_type: str = "text"`. No call site passes an explicit `chunk_type`, so the default change is the whole fixture fix.
- Add to `TestRagIngester`: write one chunk file with `_make_chunk(chunk_type="chunk")` into `chunk/`, run `ingest_all()` with the embedding service stubbed, and assert that the file no longer exists in `chunk/`, that `{stem}.error.json` exists in `failed/` (guaranteed by the seq-7 document), and that no `chunks` row was written for the URL.

### Details
- The rejection reaches `failed/` through the existing path: `read_chunk_json` raises `ChunkFormatError` → `ChunkGroupingStrategy.group()` reports `(path, IngestionFailureReason.PARSE_FAILED)` (`scripts/rag/ingestion/chunk_grouping.py` L78-88) → `RagIngester.ingest_all` routes it at `scripts/rag/ingestion/ingester.py` L162-163 via `_route_group_failed` (L395-399). No new code path is asserted here.
- The stub embeddings in this file are already 1024-length or unused by the affected tests, so the seq-1 embedding-size change does not require fixture changes here (measured: 0 failures under the embedding-size patch alone).

## Compatibility considerations

- Fixture default change plus one added test; no existing assertion is weakened.

## Security considerations
N/A: test data only.

## Rollback considerations
N/A: revert the single commit.

## Validation plan

- `uv run pytest tests/rag/ingestion/test_rag_ingester.py -q` — the 4 measured failing names are green after the fixture change, before the production change lands.
- The new rejection-routing case fails on HEAD (the out-of-domain payload is ingested or rejected at commit) and passes after the seq-2 change; its sidecar assertion depends on the seq-7 change.
- `uv run pytest tests/rag/ingestion -q` regression.

## Completion criteria

- The 4 measured failing test names pass, and a chunk file with `chunk_type="chunk"` ends in `failed/` with a `.error.json` sidecar and no `chunks` row (AC-2).

## Out of Scope

- `scripts/rag/ingestion/ingester.py` behavior (seq-3 document).
- The `.error.json` content shape (seq-7 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261110-115136 | 20261110-115136 | Test-only procedure: no production change |
| 2 | Add or update tests per Validation plan | Completed | 20261110-115136 | 20261110-115136 | check_consistency patched (ingest_all builds real DocumentManager internally) |
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
- **Requirement ID**: `REQ-002` (reject out-of-schema `chunk_type` at read time)
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-232810
- **Related target files**: `tests/rag/ingestion/test_rag_ingester.py`