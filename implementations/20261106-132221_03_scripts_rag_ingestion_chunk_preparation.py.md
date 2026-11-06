## Goal
Count the `embed_failed` metric by enum identity instead of a substring of the reason text (`REQ-003`).

## Scope
**Release unit**: retry-tier-removal

- In scope: the one condition in `ChunkFactory.prepare` that increments `embed_failed`.
- Out of scope: the exception-path reasons (`str(e)`), `_embed_and_store`, and every other function.

## Assumptions
- Verified on 2026-11-06 (Step 3a): in `prepare`, the branch for a result that is an `IngestionFailureReason` computes `reason_str = result.value ...` and increments `embed_failed` when `"embedding" in reason_str.lower()`; the only enum member whose value contains `embedding` is `EMBEDDING_FAILED` (`embedding_failed`), so identity and substring select the same members today and the metric's observable semantics do not change. `test_ingest_url_group_embed_failed_count` in `tests/rag/ingestion/test_ingester.py` pins the metric.
- Design 2 was approved by the operator on 2026-11-06 (Plan UNK-01 resolved): remove the `retry/` tier; every failed chunk goes to `failed/` with its `.error.json`.
- Release unit `retry-tier-removal` (Plan phases 1 and 2) has three members in `seq` order: the test file first (its flipped assertions fail until the code lands), then `file_routing.py`, then `chunk_preparation.py`; the end-of-unit run is the single full-suite run (`skills/code-implementation/workflow.md` Batch mode).
- Overlap: the 003 Plan's procedures (not yet executed) also edit `scripts/rag/ingestion/ingester.py` (group-failure routing) and the lifecycle row of `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`; they do not edit `file_routing.py`, `chunk_preparation.py`, or this test file's retry tests. This Plan goes first (Plan Design) and the 003 documentation procedure rewrites the same row afterwards.
- Step 3a (2026-11-06, HEAD `97b8f4f6b`): `RagIngester.ingest_url_group` passes the fixed reason string `embedding_partial_failure` (not an `IngestionFailureReason` member) for each prepared chunk of a group that also had a failed chunk; the Plan was corrected so this known production reason is accepted without a `WARNING`.

## Design decisions
- Replace the condition by `result is IngestionFailureReason.EMBEDDING_FAILED`; keep `reason_str` for the failed-path entry.

## Alternatives considered
N/A: single-condition change.

## Implementation
### Target file
`scripts/rag/ingestion/chunk_preparation.py`

### Procedure
1. In `ChunkFactory.prepare`, replace `if "embedding" in reason_str.lower():` by `if result is IngestionFailureReason.EMBEDDING_FAILED:`.
2. Confirm `rg '"embedding" in' scripts/rag/` is empty and run the ingestion tests.

### Method
- No other statement of the function changes.

### Details
- `IngestionFailureReason` is already imported in the module.

## Compatibility considerations
- The `embed_failed` count is unchanged for every enum reason.

## Security considerations
N/A: no input handling.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py` (the unit's end-of-unit run follows).
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run radon cc scripts/rag/ingestion/chunk_preparation.py -s` (no C-or-worse grade).
- At the end of the release unit: the single full-suite run with coverage, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`, and `uv run python tools/run_validation_gates.py`.

## Completion criteria
- No substring classification remains under `scripts/rag/` (`rg` scan empty); the metric test passes unchanged; the end-of-unit run and diff-cover pass.

## Out of Scope
- Exception-path reasons and any other function.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the substring condition by enum identity | Pending | — | — | |
| 2 | Run the ingestion tests | Pending | — | — | |
| 3 | At the end of the release unit run the validation sequence (`rules/toolchain.md`), the single full-suite run, and diff-cover | Pending | — | — | |
| 4 | N/A: documentation is another procedure of this Plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (enum-identity counting)
- **Source issue**: issues/20261106-073538_raging005_retry-dir-no-consumer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-102010_raging005_retry-dir-no-consumer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-132221
- **Related target files**: `scripts/rag/ingestion/chunk_preparation.py`
