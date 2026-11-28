## Goal

Add the mixed-root cases measured through the query boundary: unauthorized rows ranked above authorized rows, and the shrink-allowlist behavior observed through the SQL predicate rather than the Python post-`LIMIT` filter (REQ-002, AC-1).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- This row keeps its own document because it fails the companion condition (2): no code row in this plan names it, and it is already the companion of `implementations/20261127-213547_02_scripts_mcp_servers_mdq_mdq_service.py.md` in plan 001, so it cannot be a companion of a second document.
- Written in Phase 1 before the production change; the added assertions fail first because the current authorization runs after `LIMIT`.
- The existing assertions stay unchanged: `test_narrowed_allowed_dirs_hides_indexed_content` (line 57) and `test_deny_all_returns_no_matches_not_unfiltered_scan` (line 142) (re-cited 20261128 against current source).
- Corrected 20261128: only the count assertion fails first. The row-presence assertion passes before the change, because the post-`LIMIT` Python filter already removes the unauthorized row; the failing-first assertion is on `matched_count` measured through `_search_docs_structured()`, which is the database-wide count today.
- Execution-order dependency on plan 001: resolved 20261128 - its procedures have been executed and archived; the gated markers this document carried were cleared by owner decision on 20261128 (recorded in Execution Status Notes). `tools/plan_dependency_order.py` reports this plan Ready.

## Design decisions
- The mixed-root fixture indexes rows under two roots and authorizes one, so the unauthorized row is present in the database and can only be excluded by the SQL predicate.
- The shrink-allowlist case is measured through the query boundary, so it verifies the predicate rather than the Python filter.

## Alternatives considered
- Reuse the single-root fixture — rejected: a single root cannot produce a row that is indexed but unauthorized, which is the case the requirement needs.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_read_authorization.py`

### Procedure
- Add the mixed-root case: an unauthorized row ranked above an authorized row.
- Add the shrink-allowlist case measured through the query boundary.
- Keep the existing assertions unchanged.

### Method
- Ranking is made deterministic by indexing content whose bm25 score places the unauthorized row first, so the assertion does not depend on insertion order.

### Details
- The file's existing async fixtures are reused; no new fixture is introduced.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- This file is the AC-1 guard for the read-authorization path through the query boundary.

## Rollback considerations
- N/A: revert the commit; the added tests fail again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_read_authorization.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- An unauthorized row cannot appear in the results or change the count.
- Shrinking the allowlist immediately removes prior-root information through the query boundary.

## Out of Scope
- The SQL predicate (seq 01) and the canonicalized roots (seq 02).
- The stats refusal, which plan 001 covers through the same file.
- Verified 20261128: plan 001's stats rows already exist in this file (`test_stats_refused_when_no_roots_are_authorized`, line 160; `test_shrunk_allowlist_removes_prior_root_counts`, line 173) and pass, so this procedure adds only the search-boundary cases and does not re-add them.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261128-115500 | Gated marker cleared 20261128 by owner decision: the blocking plan plans/20261127-160114_mdqmcp001_mdq-server-boundary.md was executed and archived and plan_dependency_order.py reports this plan Ready - Depends on plan 001 procedures, which have landed and are archived Red-first confirmed 20261128: test_mixed_roots_unauthorized_row_ranked_first fails (unauthorized row takes the slot) and test_shrunk_allowlist_reported_zero_through_the_query_boundary fails at matched_count 1 != 0; 3 existing guards pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-134500 | 20261128-134500 | Both red tests green after the seq 01 predicate; member run 6 passed; gates clean; full suite once at end of unit, baseline-only failures. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-002 (mixed-root authorization through the query boundary)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_read_authorization.py`
