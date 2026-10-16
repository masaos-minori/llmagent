## Goal
- `REQ-002`: lock pinned/unpinned handling of `top_semantic()` with real-SQLite tests.
- `REQ-003`: show that `MemoryInjectionService.on_session_start()` over a real retriever returns a pinned low-importance memory.

## Scope
- Add tests to `tests/agent/memory/test_memory_retriever.py` only. The query change is the other row's document (`scripts/agent/memory/retriever.py`).

## Assumptions
- Pinned entries bypass `min_importance` (Plan Assumptions); the tests encode that rule.
- The existing `retriever` and `db_conn` fixtures and the `_insert` helper (which accepts `pinned`) are enough; no new fixture is needed.

## Design decisions
- Extend `TestTopSemantic` for retriever-level cases; put the injection case in a new class so mock-based `test_memory_layer.py` stays unchanged.
- Build `MemoryInjectionService` with the `retriever` fixture and a `MagicMock(spec=EmbeddingClient)` for `embed_client`, since `on_session_start()` never calls the embedder.

## Alternatives considered
N/A: more mock-based tests in `test_memory_layer.py` were rejected because they cannot detect the SQL predicate defect.

## Implementation
### Target file
`tests/agent/memory/test_memory_retriever.py`

### Procedure
- In `TestTopSemantic`, add `test_pinned_below_threshold_is_returned` (new): pinned=1, importance 0.2, `top_semantic(min_importance=0.5)` includes it.
- Add `test_unpinned_below_threshold_is_excluded` (new): pinned=0, importance 0.2, same call excludes it.
- Add `test_pinned_returned_first_under_limit` (new): insert several unpinned rows at higher importance plus one pinned row at lower importance, call with `limit=2`, assert the pinned row is first and the result has 2 entries. The existing `test_pinned_entry_ordered_first` covers ordering without a limit and stays as is.
- Add class `TestSessionStartPinnedInjection` (new) with `test_pinned_low_importance_memory_is_injected` (new): insert one pinned row at importance 0.2, build `MemoryInjectionService(policy=InjectionPolicy(min_importance=0.5), retriever=retriever, embed_client=MagicMock(spec=EmbeddingClient))`, assert `on_session_start()` returns one snippet whose text contains the row's summary.

### Method
- Insert rows with `_insert(db_conn, memory_id=..., memory_type="semantic", importance=..., pinned=...)`; assert on `[e.memory_id for e in entries]` as the neighbouring tests do.
- Add the imports the injection test needs at the top of the module (`InjectionPolicy`, `MemoryInjectionService` from `agent.memory.injection`; `EmbeddingClient` from `agent.memory.embedding_client`; `MagicMock` from `unittest.mock`) if not already imported.

### Details
- Run the new tests before the `retriever.py` edit; the pinned-below-threshold test and the session-start injection test must fail, and the other two follow the current query. Record the observed result in Notes.
- Tests must not touch a production DB; they use the in-memory fixtures only.

## Compatibility considerations
N/A: additive tests; no existing test is edited.

## Security considerations
N/A: test-only change with no secrets or external access.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/memory/test_memory_retriever.py -v` (new tests fail before and pass after the `retriever.py` edit)
- `uv run ruff format tests/agent/memory/test_memory_retriever.py`, `uv run ruff check tests/agent/memory/test_memory_retriever.py`
- `uv run python tools/check_mock_patch_targets.py` and `uv run coverage run -m pytest tests/` then `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`

## Completion criteria
- The four new tests exist and pass after the `retriever.py` change; the pinned-below-threshold test and the injection test fail beforehand.
- The existing tests in the file, `test_memory_layer.py`, and `test_regression_memory_branch.py` still pass.
- Diff coverage on changed lines is at least 90%.

## Out of scope
- Editing `test_memory_layer.py`, pinned episodic memories (UNK-01), the `max_semantic` versus `memory_max_pinned` cap (UNK-02), and any `docs/*.md` edit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three retriever-level tests to `TestTopSemantic` | Completed | 20261016-101133 | 20261016-101409 | changed: tests/agent/memory/test_memory_retriever.py |
| 2 | Add the session-start injection test class and required imports | Completed | 20261016-101409 | 20261016-101409 | added TestSessionStartPinnedInjection and imports |
| 3 | Run the new tests and confirm the two pinned-below-threshold cases fail first | Completed | 20261016-101409 | 20261016-101409 | red check with old predicate: 3 failed (below-threshold, limit, injection); the limit test also failed, beyond the 2 expected |
| 4 | Run the validation sequence (`rules/toolchain.md`) after the `retriever.py` edit | Completed | 20261016-101409 | 20261016-101409 | ruff clean; mypy 18 errors in this file identical to baseline; 107 related tests passed; tests/agent/memory 401 passed; diff-cover reported no coverage lines for the diff; full suite 57 pre-existing session-undo failures |

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
- **Requirement ID**: REQ-002 (retriever-level pinned tests), REQ-003 (session-start injection test)
- **Source issue**: issues/20261016-092648_mem002_add-pinned-memory-session-start-injection-test.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-093429_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-095005
- **Related target files**: tests/agent/memory/test_memory_retriever.py