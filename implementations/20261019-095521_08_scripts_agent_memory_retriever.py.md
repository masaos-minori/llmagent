## Goal
Make `VectorRetriever.knn_search` issue a KNN query that vec0 accepts once the extension is loaded, so hybrid retrieval can work (`REQ-009`).

## Scope
- The SQL string and parameter list inside `VectorRetriever.knn_search`.
- The return shape, the negated-L2 score convention, the type and branch filters, and `HybridRetriever` stay as they are.

## Assumptions
- Verified on 2026-10-19 against a real vec-enabled session database: the current query fails with `A LIMIT or 'k = ?' constraint is required on vec0 knn queries`; a subquery with `k = ?` joined afterward to `memories` returns the nearest rows.
- `HybridRetriever.search` passes the FTS candidate limit as `limit`, so `k` equals that limit (Plan UNK-05).

## Design decisions
- Bound the KNN with `k = ?` inside a subquery and join `memories` afterward, keeping the type and branch filters on the outer query: the smallest change vec0 accepts.
- The filters therefore apply after the KNN bound and can return fewer than `limit` rows; accepted and recorded by the real-DB test rather than hidden.

## Alternatives considered
Filtering by joining before the KNN was rejected: vec0 needs the bound on the vec0 scan itself. Over-fetching a multiple of `limit` was deferred as a follow-up (Plan UNK-05) to keep this change minimal.

## Implementation
### Target file
`scripts/agent/memory/retriever.py`

### Procedure
1. Rewrite the SQL in `VectorRetriever.knn_search` so the inner query is `SELECT memory_id, distance FROM memories_vec WHERE embedding MATCH ? AND k = ?` and the outer query joins `memories` with the existing type and branch filters, `ORDER BY` distance, and `LIMIT ?`.
2. Adjust the parameter list to the new placeholder order: blob, `k`, then the existing type and branch parameters, then the outer `LIMIT`.
3. Keep the existing `# nosec B608` justification valid (filters remain literal strings; values use placeholders).

### Method
- `_build_query_params` returns [primary, optional type, optional branch twice, limit]; insert `k` (the same `limit` value) directly after the primary parameter instead of changing the shared helper, which the FTS path also uses.
- Select the same columns as today (`m.*` fields plus `distance`) so `row_to_entry` and the score negation need no change.
- Use the exact query verified in the Assumptions as the starting point.

### Details
- The real-DB test in `tests/agent/memory/test_memory_vec_session.py` is the acceptance check; existing tests mock `knn_search` and do not depend on the SQL text.
- Do not alter `FtsRetriever`, `HybridRetriever`, RRF merging, or the score convention.

## Compatibility considerations
No signature or return change. Result sets may contain fewer than `limit` rows when many nearest rows are filtered out (new, documented); before this change the call always raised once the extension loaded.

## Security considerations
The SQL remains parameterized; the only interpolated pieces are the literal filter fragments from `_build_filters`.

## Rollback considerations
Revert the commit; KNN then raises `OperationalError` again and retrieval degrades to FTS-only with a WARNING, as before.

## Validation plan
- `uv run pytest tests/agent/memory/test_memory_vec_session.py tests/agent/memory/test_memory_retriever.py -q`
- `uv run ruff check scripts/agent/memory/retriever.py`, `uv run mypy`, `uv run bandit scripts/agent/memory/retriever.py`

## Completion criteria
- `knn_search` returns the expected nearest entries on a real vec-enabled database, honoring type and branch filters.
- `HybridRetriever.search` with an embedding reports hybrid mode on that database.
- Existing retriever tests pass unchanged.

## Out of scope
- Ranking, score, or RRF changes
- Over-fetch tuning (follow-up, Plan UNK-05)
- Changing `_build_filters` or `_build_query_params`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the KNN SQL and parameter order in `knn_search` | Pending | — | — | |
| 2 | Confirm the real-DB KNN and hybrid tests pass and the mocked retriever tests are unchanged | Pending | — | — | |
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
- **Requirement ID**: `REQ-009` (vec0-valid KNN query)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: scripts/agent/memory/retriever.py
