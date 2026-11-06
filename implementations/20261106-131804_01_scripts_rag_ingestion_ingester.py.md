## Goal
Bump the corpus `index_generation` in `RagIngester.ingest_all` only when at least one URL group wrote content in the run, so that all-failed and skipped-only runs stop advancing the cache-invalidation signal (`REQ-001`: content-based guard; `REQ-002`: regression and characterization tests; `REQ-003`: bump contract unchanged).

## Scope
**Release unit**: generation-bump-guard

- In scope: the guard condition and its comment in `ingest_all`, hoisting the existing `total_success` computation above it, and four new tests in the companion test file.
- Out of scope: consumers of `index_generation`, bump granularity (stays per run), `bump_index_generation` itself (`scripts/rag/corpus_identity.py`), `TransactionManager`, and the 003 Plan's routing changes.

## Assumptions
- Verified on 2026-11-06 (Step 3a, HEAD `97b8f4f6b`): inside the `with SQLiteHelper(...).open(...)` block of `ingest_all`, after `check_consistency`, the guard is `if results and any(not r.skipped for r in results): bump_index_generation(db)`; `total_success = sum(r.n_success for r in results)` is computed after the block and used by the summary log. Every failure result (`validation_failure`, `unexpected_failure`, the two `GROUP_VALIDATION_FAILED` results, all-embed-failed) has `skipped=False` and `n_success=0`. `ingest_url_group` runs the transaction only when `len(prepared_chunks) > 0 and len(failed_paths) == 0` and then `n_success = len(prepared_chunks)`, otherwise `0`, so `sum(n_success) > 0` is exactly "at least one group wrote content". `_process_url_groups` catches `(OSError, RuntimeError, ValueError, sqlite3.Error)` and returns `unexpected_failure`.
- Plan correction recorded in the Plan (Step 3a): the `n_success` expression is `len(prepared_chunks) if len(failed_paths) == 0 else 0`; the equivalence is unchanged.
- Companion test file `tests/rag/ingestion/test_ingester_index_generation.py`: a valid companion because it is a row of the Plan under `tests/`, only the code row names it in `Related Tests`, and the Plan prescribes the tests. It has three tests today (`test_completed_ingest_advances_generation_by_one`, `test_no_chunk_files_leaves_generation_unchanged`, `test_missing_meta_table_returns_none_without_raising`) and helpers `_make_rag_db`, `_seed_generation`, `_read_generation`, `_write_chunk`, `_make_ingester`, and `_make_fake_sqlite_helper`; no all-failed or skipped-only test exists.
- Embedding failure is produced by patching `EmbeddingService.get_embedding` to return `None` (`embed_and_store` then reports `EMBEDDING_FAILED`); an unexpected failure by patching `RagIngester.ingest_url_group` to raise `sqlite3.Error`. The group-validation case needs two chunk files of one URL with mismatched group signatures written directly with the `_write_chunk` pattern (a valid payload including `code_blocks`), because `ChunkSplitter` output currently fails `read_chunk_json` (`issues/20261106-110845_ragfix001_chunk-payload-code-blocks.md`).
- Sequencing: the 003 Plan's procedure for this file (`implementations/20261106-115721_02_scripts_rag_ingestion_ingester.py.md`, not yet executed) edits `ingest_all` only to route the grouping-rejected files after grouping and `_process_url_groups` only to sort the groups; it does not touch the guard region, so the two are compatible, and its routed groups still return `n_success=0`. Either order works; the 003 Plan goes first (Plan Design).
- The Plan's release unit `generation-bump-guard` (phases 1 and 2) is covered entirely by this document (red tests, then the fix, in one cycle). Plan step 3 (gate sequence and deploy hand-off) modifies no file and is carried out by `code-implementation`; the deploy is the user's decision.

## Design decisions
- Hoist `total_success = sum(r.n_success for r in results)` to just before the guard (inside the `with` block) and use it for both the guard and the summary log, so the sum is computed once; the later statement after the block is removed.
- Guard: `if total_success > 0: bump_index_generation(db)`; the empty `results` case is covered by the same test. The bump keeps its position after the consistency check, outside any per-URL transaction, and stays best-effort.
- Reword the comment to match: advance once this run has written content (`n_success > 0` for at least one group); skipped-only and all-failed runs leave the generation untouched.

## Alternatives considered
- `any(r.n_success > 0 for r in results)`: rejected, `total_success` already exists for the summary log and one shared computation is simpler.
- A per-result flag recording that content was written: rejected, new state for no benefit given the verified equivalence.

## Implementation
### Target file
`scripts/rag/ingestion/ingester.py`

### Procedure
1. Add the four new tests to the companion test file and run it: the three all-failed tests fail against the current guard; the skipped-only test passes (characterization).
2. In `ingest_all`, move the `total_success` assignment above the guard (inside the `with` block), remove its later duplicate, and replace the guard by `if total_success > 0:`; reword the comment above it.
3. Re-run the companion file and `uv run pytest tests/rag/ingestion`.

### Method
- Edit only the run-level guard region of `ingest_all`; leave `ingest_url_group`, `_process_url_groups`, and the summary log text unchanged.

### Details
- `ingest_all` is radon grade C (16) today and `ingest_url_group` C (14); the change adds no branch, so no grade rises. Do not reduce their complexity here.
- The summary log keeps reading the same `total_success` value.

### Companion test files
- `tests/rag/ingestion/test_ingester_index_generation.py`
  - Procedure: add tests in the existing test class using the file's helpers: `test_all_embed_failed_run_leaves_generation_unchanged` (new) (new: `get_embedding` patched to return `None`), `test_group_validation_failure_leaves_generation_unchanged` (new) (new: two chunk files of one URL with mismatched group signatures), `test_unexpected_failure_leaves_generation_unchanged` (new) (new: `ingest_url_group` patched to raise `sqlite3.Error`), and `test_skipped_only_run_leaves_generation_unchanged` (new) (new: run once to register the group, then run again so every group is skipped); each seeds the generation with `_seed_generation`, runs `ingest_all` with the patched `SQLiteHelper` and consistency report as in the existing test, and asserts `_read_generation` equals its pre-run value; the existing three tests stay unchanged.
  - Validation: `uv run pytest tests/rag/ingestion/test_ingester_index_generation.py -v`: the three all-failed tests fail before step 2 and pass after it; the skipped-only test and the existing three pass throughout; then `uv run pytest tests/rag/ingestion`.

## Compatibility considerations
- A run in which some group wrote content still advances the generation exactly once; only all-failed runs stop advancing it. Consumers poll the value, so a rarer bump is safe (Plan UNK-01, non-blocking).

## Security considerations
N/A: no input handling or secrets are involved.

## Rollback considerations
- Revert the commit; the generation counter is not migrated by this change.

## Validation plan
- `uv run pytest tests/rag/ingestion/test_ingester_index_generation.py -v`, then `uv run pytest tests/rag/ingestion`.
- `uv run ruff format`, `uv run ruff check scripts/ tests/rag/ingestion`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run radon cc scripts/rag/ingestion/ingester.py -s` (no grade rises).
- Full suite once with coverage, then `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`; `uv run python tools/run_validation_gates.py`.

## Completion criteria
- All-failed runs (embedding, group validation, unexpected exception) and skipped-only runs leave `index_generation` unchanged; a run with at least one successful group advances it exactly once; the existing tests pass unchanged; the ingestion test directory passes; changed lines reach the diff-cover threshold.

## Out of Scope
- Consumers of `index_generation`, bump granularity, `bump_index_generation`, the 003 Plan's routing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the four tests and confirm the failing cases | Pending | — | — | |
| 2 | Hoist `total_success` and swap the guard in `ingest_all` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`), the radon check, and the single full-suite run with coverage | Pending | — | — | |
| 4 | N/A: no documentation change (Plan Documentation Impact is N/A) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (content-based guard), `REQ-002` (tests), `REQ-003` (bump contract unchanged)
- **Source issue**: issues/20261106-073538_raging006_fix-index-generation-bump.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261106-102751_raging006_fix-index-generation-bump.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-131804
- **Related target files**: `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester_index_generation.py`
