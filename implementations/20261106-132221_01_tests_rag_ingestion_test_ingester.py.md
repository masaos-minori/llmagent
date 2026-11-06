## Goal
Flip the three tests that pin the `retry/` destination to the two-terminal-directory design and add the never-`retry/` and unknown-reason `WARNING` tests (`REQ-004`).

## Scope
**Release unit**: retry-tier-removal

- In scope: the three retry-destination tests and two new tests in this file.
- Out of scope: every other test of the file, and the production changes (the next two procedures).

## Assumptions
- Verified on 2026-11-06 (Step 3a): `test_embedding_failure_moves_to_retry_not_registered`, `test_mixed_success_and_failure_routes_correctly`, and `test_retry_directory_created_for_embedding_failures` assert the files under `retry/` (the first and third with a single embedding-failed chunk and a patched `_client.post` returning an empty embedding; the second with a prepared and a failed chunk, both ending in `retry/`); `test_ingest_url_group_embed_failed_count` pins the `embed_failed` metric and stays unchanged. The file uses the helpers `_make_db`, `_write_chunk`, and `_make_ingester`; log assertions in this directory patch the module `logger` (for example `patch("rag.ingestion.etag_manager.logger")`).
- This file is not a companion: its row is named in `Related Tests` by two code rows of the Plan (`file_routing.py` and `chunk_preparation.py`), so it keeps its own procedure.
- Design 2 was approved by the operator on 2026-11-06 (Plan UNK-01 resolved): remove the `retry/` tier; every failed chunk goes to `failed/` with its `.error.json`.
- Release unit `retry-tier-removal` (Plan phases 1 and 2) has three members in `seq` order: the test file first (its flipped assertions fail until the code lands), then `file_routing.py`, then `chunk_preparation.py`; the end-of-unit run is the single full-suite run (`skills/code-implementation/workflow.md` Batch mode).
- Overlap: the 003 Plan's procedures (not yet executed) also edit `scripts/rag/ingestion/ingester.py` (group-failure routing) and the lifecycle row of `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`; they do not edit `file_routing.py`, `chunk_preparation.py`, or this test file's retry tests. This Plan goes first (Plan Design) and the 003 documentation procedure rewrites the same row afterwards.
- Step 3a (2026-11-06, HEAD `97b8f4f6b`): `RagIngester.ingest_url_group` passes the fixed reason string `embedding_partial_failure` (not an `IngestionFailureReason` member) for each prepared chunk of a group that also had a failed chunk; the Plan was corrected so this known production reason is accepted without a `WARNING`.

## Design decisions
- Rename the flipped tests so their names no longer say `retry`: `test_embedding_failure_moves_to_failed_not_registered` (new) and `test_retry_directory_is_never_created` (new); keep `test_mixed_success_and_failure_routes_correctly`.
- The unknown-reason test calls `FileRouter.route` directly, so it needs no ingester fixture.

## Alternatives considered
- Keep the old test names with changed assertions: rejected, a name that says `retry` after the tier is removed misleads.

## Implementation
### Target file
`tests/rag/ingestion/test_ingester.py`

### Procedure
1. Rewrite `test_embedding_failure_moves_to_retry_not_registered` as `test_embedding_failure_moves_to_failed_not_registered` (new): assert `failed/c.json` and `failed/c.error.json` exist, `retry/` does not exist, and the chunk is not in `registered/`.
2. In `test_mixed_success_and_failure_routes_correctly` assert both the prepared and the failed chunk end in `failed/` (with `.error.json`), no `retry/` directory exists, and, with the module `logger` of `rag.ingestion.file_routing` patched, no `warning` is logged for the `embedding_partial_failure` reason.
3. Replace `test_retry_directory_created_for_embedding_failures` by `test_retry_directory_is_never_created` (new): after a run with an embedding failure and after a run with none, `rag-src/retry` does not exist.
4. Add `test_route_unknown_reason_warns_and_goes_to_failed` (new): build a `FileRouter` over a temporary `chunk/` directory, call `route([], [(path, "some httpx error text")])` with the module `logger` patched, assert a `warning` call naming the reason and the file in `failed/`.
5. Run the file: the three flipped tests and the new unknown-reason test fail until the production procedures land (allowed red state inside the release unit); every other test passes.

### Method
- Reuse the existing helpers and patching style; do not change `test_ingest_url_group_embed_failed_count` or any other test.

### Details
- Update the docstrings of the flipped tests: they must no longer mention `retry/`.
- The `.error.json` assertion uses the file name `{stem}.error.json` next to the moved chunk in `failed/`.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: temporary directories only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_ingester.py -v` (red until the code procedures land), then after them `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py`.
- `uv run ruff format`, `uv run ruff check tests/rag/ingestion`, `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria
- The flipped and new tests exist with the assertions above, pass once the production procedures are applied, and no test of the file mentions `retry/` as a destination.

## Out of Scope
- Production code and documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Flip the three tests and add the unknown-reason test | Completed | 20261106-163353 | 20261106-163353 |  |
| 2 | Run the file and record the expected red state (release unit) | Completed | 20261106-163353 | 20261106-163353 |  |
| 3 | Run the validation sequence at the end of the unit (`rules/toolchain.md`) | Completed | 20261106-163353 | 20261106-163353 |  |
| 4 | N/A: documentation is another procedure of this Plan | Completed | 20261106-163353 | 20261106-163353 |  |

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
- **Requirement ID**: `REQ-004` (flipped and new tests)
- **Source issue**: issues/20261106-073538_raging005_retry-dir-no-consumer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-102010_raging005_retry-dir-no-consumer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-132221
- **Related target files**: `tests/rag/ingestion/test_ingester.py`