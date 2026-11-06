## Goal
Remove the `retry/` tier from `FileRouter.route`: every failed chunk goes to `failed/` next to its `.error.json`, classification no longer depends on the reason text, and an unknown reason is logged at `WARNING` (`REQ-001`, `REQ-002`).

## Scope
**Release unit**: retry-tier-removal

- In scope: the module, class, and `route()` docstrings, the `retry_dir` creation and branch, the substring test, and a `WARNING` for unknown reasons.
- Out of scope: the `route()` signature, `write_error_metadata`, `ingester.py`, `transaction_commit.py`, and any cleanup of an existing `retry/` directory.

## Assumptions
- Verified on 2026-11-06 (Step 3a): `route()` creates `retry/` and `failed/` on every call, writes `.error.json` into `failed/` for each failed chunk, and moves the chunk to `retry/` when `"embedding" in reason.lower()`, otherwise to `failed/`; the module and `route()` docstrings describe `retry/`; `IngestionFailureReason` (`scripts/rag/exceptions.py`) is a `StrEnum` with the members `PARSE_FAILED`, `VALIDATION_FAILED`, `EMBEDDING_FAILED`, `STORAGE_FAILED`, `UNEXPECTED_FAILURE`, and `GROUP_VALIDATION_FAILED`. The only production reasons that are not enum values are exception text (`str(e)` from `chunk_preparation.py`) and `embedding_partial_failure` (from `ingester.py`). No reader of `retry/` exists in `scripts/`, `tests/`, `docs/`, or `deploy/` (`rg` scan), and `/opt/llm/rag-src/` has no `retry/` at plan time.
- Design 2 was approved by the operator on 2026-11-06 (Plan UNK-01 resolved): remove the `retry/` tier; every failed chunk goes to `failed/` with its `.error.json`.
- Release unit `retry-tier-removal` (Plan phases 1 and 2) has three members in `seq` order: the test file first (its flipped assertions fail until the code lands), then `file_routing.py`, then `chunk_preparation.py`; the end-of-unit run is the single full-suite run (`skills/code-implementation/workflow.md` Batch mode).
- Overlap: the 003 Plan's procedures (not yet executed) also edit `scripts/rag/ingestion/ingester.py` (group-failure routing) and the lifecycle row of `docs/21_rag/rag_02_01_ingestion_pipeline-overview.md`; they do not edit `file_routing.py`, `chunk_preparation.py`, or this test file's retry tests. This Plan goes first (Plan Design) and the 003 documentation procedure rewrites the same row afterwards.
- Step 3a (2026-11-06, HEAD `97b8f4f6b`): `RagIngester.ingest_url_group` passes the fixed reason string `embedding_partial_failure` (not an `IngestionFailureReason` member) for each prepared chunk of a group that also had a failed chunk; the Plan was corrected so this known production reason is accepted without a `WARNING`.

## Design decisions
- Delete the `retry_dir` creation and branch; the destination of every failed chunk is `failed/`.
- Classification: a reason is known when `IngestionFailureReason(reason)` succeeds (catch `ValueError`) or when it is in a small module-level collection of known non-enum production reasons that contains `embedding_partial_failure`; any other reason logs a `WARNING` naming the reason, then routes to `failed/` as usual.
- The collection is private to this module and documented by a one-line comment naming its source (`ingester.py`).

## Alternatives considered
- Add `embedding_partial_failure` to `IngestionFailureReason`: rejected, it would change a shared enum and `exceptions.py` is not a target of this Plan.
- Log every non-enum reason at `DEBUG`: rejected, exception text deserves a visible warning.

## Implementation
### Target file
`scripts/rag/ingestion/file_routing.py`

### Procedure
1. Update the module docstring, the class docstring if it mentions `retry/`, and the `route()` docstring to the two-destination description (`registered/` on success, `failed/` with `.error.json` on failure).
2. Delete the `retry_dir` assignment and `mkdir`, and the `if "embedding" in reason.lower()` branch; set `dest = failed_dir / path.name` for every failed chunk.
3. Add the private collection `_KNOWN_NON_ENUM_REASONS` (new) with `embedding_partial_failure` and a small private helper `_is_known_reason` (new) that returns true for an enum value or a collection member; import `IngestionFailureReason` from `rag.exceptions` next to the existing import.
4. In the failed-paths loop, call the helper and log `logger.warning(...)` with the reason when it returns false.
5. Confirm `rg '"embedding" in' scripts/rag/ingestion/file_routing.py` is empty and run the test file.

### Method
- Keep the `.error.json` writing and the move code unchanged; only the destination selection and the warning change.

### Details
- `route()` keeps the signature `route(self, successful_paths, failed_paths)`; the callers in `ingester.py` and `transaction_commit.py` are unchanged.
- Do not delete an existing `retry/` directory; that is an operator task.

## Compatibility considerations
- A chunk that fails embedding now lands in `failed/` instead of `retry/`; nothing reads `retry/`, so no consumer is affected. The public signature is unchanged.

## Security considerations
N/A: no new input; paths come from the pipeline's own directories.

## Rollback considerations
- Revert the commit; files already moved to `failed/` stay there.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_ingester.py -v` (green after this procedure and the next), `uv run pytest tests/rag/ingestion tests/integration/test_ingestion_e2e.py`.
- `uv run ruff format`, `uv run ruff check scripts/ tests/rag/ingestion`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`.
- `uv run rg '"embedding" in' scripts/rag/` returns nothing after the next procedure (AC-2).

## Completion criteria
- No `retry` directory is created or used by `file_routing.py`; every failed chunk is in `failed/` with `.error.json`; no substring classification remains in the file; an unknown reason logs a `WARNING` and `embedding_partial_failure` does not.

## Out of Scope
- `ingester.py`, `chunk_preparation.py`, `exceptions.py`, documentation.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the retry branch and update the docstrings | Pending | — | — | |
| 2 | Add the enum-based classification and the warning | Pending | — | — | |
| 3 | Run the validation sequence at the end of the unit (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: `REQ-001` (remove the `retry/` tier), `REQ-002` (enum-based classification and warning)
- **Source issue**: issues/20261106-073538_raging005_retry-dir-no-consumer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-102010_raging005_retry-dir-no-consumer.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-132221
- **Related target files**: `scripts/rag/ingestion/file_routing.py`
