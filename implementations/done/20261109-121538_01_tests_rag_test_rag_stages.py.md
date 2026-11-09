## Goal
Pin the independent-leg contract of `SearchStage` with tests written first (`REQ-001`: embedding outage still returns lexical hits; `REQ-002`: a vector error does not suppress FTS hits; `REQ-003`: each failed leg is counted once; `REQ-006`: tests that encode the old coupling are updated explicitly, the pinned test stays unmodified).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/rag/test_rag_stages.py`. Production code and docs are changed by the next two procedures of the same Plan.

## Assumptions
- Execution order: Plan Phase 1, before `scripts/rag/stages/search.py`. The new tests must fail on the current HEAD for the reason the Plan names (the FTS call is skipped or lost).
- Overlap judgment (Plan Assumptions): `plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md` also adds tests to this file; it is a sequencing dependency (it lands after this Plan), so these tests use distinct names and do not touch MQE tests.
- Why this row is not a companion of the `search.py` document: the test design (which stubs, which counter values) is a decision of its own, and the Plan orders tests before code.
- `test_run_embedding_not_list` is not edited: it does not patch `RagRepository`, so the real `fts_search` runs over the `mock_db` fixture and returns `[]` (verified against a mock database at procedure time).
- The fourth new test (vector hits survive an FTS failure) is implied by `REQ-003` and `AC-3` (each leg counted separately): at HEAD both legs share one `try`, so an FTS exception also discards the vector hits.

## Design decisions
- Reuse the existing patch pattern of this file (`patch("rag.llm_client.get_embedding", new_callable=AsyncMock)` and `patch("rag.stages.search.RagRepository")` with `SimpleNamespace(top_k_search=10)`), so the new tests read like their neighbors.
- Give the stubbed `vector_search` and `fts_search` distinct, recognizable hit payloads so the assertions prove which leg produced which list.

## Alternatives considered
N/A: test-only row; a real `vec0` database test is optional only for Plan UNK-01 (dimension-mismatch exception type) and is reported, not required, here.

## Implementation
### Target file
`tests/rag/test_rag_stages.py`

### Procedure
1. Add four tests to `TestSearchStage`: `test_all_embeddings_fail_returns_fts_hits` (new), `test_vector_error_still_returns_fts_hits` (new), `test_both_legs_fail_counts_two_errors` (new), and `test_fts_error_keeps_vector_hits` (new).
2. Update `test_run_search_exception`: add an explicit `mock_repo_instance.fts_search.return_value = []` before the stage runs, so its `search_results == []` assertion is about the vector failure and no longer about a skipped FTS call.
3. Add the same explicit empty FTS stub to `test_fts_error_counts` and `test_warning_emitted_on_fts_error` (clarity only; their assertions are unchanged).
4. Do not modify `test_run_pack_failure_degrades`, `test_run_embedding_not_list`, or any `test_diagnostics.py` / `test_stage_observability.py` test.

### Method
- `test_all_embeddings_fail_returns_fts_hits` (new): two queries, `get_embedding` raises for both, `fts_search.return_value` is one hit list; assert `search_results` holds the FTS lists (one per query), `embed_failed == 2`, `embed_ok == 0`, `degraded is True`, `fts_errors == 0`, and `vector_search` was never called (AC-1).
- `test_vector_error_still_returns_fts_hits` (new): `vector_search.side_effect = sqlite3.OperationalError(...)`, `fts_search` returns hits; assert the FTS hits are in `search_results`, `fts_errors == 1` (AC-2).
- `test_both_legs_fail_counts_two_errors` (new): vector raises `ValueError`, FTS raises `sqlite3.OperationalError`; assert `fts_errors == 2`, `search_results == []`, `degraded is True` (AC-3).
- `test_fts_error_keeps_vector_hits` (new): vector returns hits, FTS raises; assert the vector hits are present and `fts_errors == 1`.
- The existing pinned test (`vector_search` raising once for one query, `fts_search` returning `[]`) must still report `fts_errors == 1`.

### Details
- Use `SimpleNamespace(top_k_search=10)` for the config and the `mock_context` / `mock_db` fixtures already in the file.
- Hit payloads follow the dict shape already used in the file (`{"chunk_id": 1, "content": "..."}`).
- Do not assert on log text beyond what existing tests already assert.

## Compatibility considerations
N/A: test-only; no public symbol changes.

## Security considerations
N/A: tests use mock repositories and dummy data.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Before the production change: `uv run pytest tests/rag/test_rag_stages.py -q`; the four new tests must fail on HEAD (record the failing assertions); `test_run_pack_failure_degrades` passes.
- After `search.py` is changed: the same command is green, then `uv run pytest tests/rag/test_diagnostics.py tests/rag/test_stage_observability.py tests/rag/test_rag_quality_regression.py -q` unmodified.
- `uv run ruff check tests/rag/test_rag_stages.py`; `uv run python tools/check_mock_patch_targets.py`.

## Completion criteria
- The four new tests exist and fail on the pre-change HEAD; after `search.py` is changed they pass.
- `test_run_search_exception`, `test_fts_error_counts`, and `test_warning_emitted_on_fts_error` carry an explicit empty FTS stub; the pinned test and `test_run_embedding_not_list` are byte-for-byte unchanged.

## Out of Scope
- `scripts/rag/stages/search.py`, the docs, MQE tests and the embedding semaphore (ragrev007), FTS query construction (ragrev005), and a `vec0` real-database dimension-mismatch test (Plan UNK-01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the four new tests and the explicit empty FTS stubs | Completed | 20261109-145634 | 20261109-145634 | Validated: 4 new tests red on HEAD then green; gates clean (ruff/mypy/lint-imports/bandit/radon B/module-size/mock-targets/ast-grep); diff-cover 100%; doc checkers pass. |
| 2 | Run the new tests on the pre-change HEAD and record that they fail | Completed | 20261109-145634 | 20261109-145634 | Validated: 4 new tests red on HEAD then green; gates clean (ruff/mypy/lint-imports/bandit/radon B/module-size/mock-targets/ast-grep); diff-cover 100%; doc checkers pass. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-145634 | 20261109-145634 | Validated: 4 new tests red on HEAD then green; gates clean (ruff/mypy/lint-imports/bandit/radon B/module-size/mock-targets/ast-grep); diff-cover 100%; doc checkers pass. |

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
- **Requirement ID**: `REQ-001` (embedding outage keeps lexical hits), `REQ-002` (vector error keeps FTS hits), `REQ-003` (per-leg counting), `REQ-006` (explicit test updates)
- **Source issue**: issues/20261108-131007_ragrev004_search-bm25-coupling.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164823_ragrev004_search-bm25-coupling.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-121538
- **Related target files**: `tests/rag/test_rag_stages.py`
