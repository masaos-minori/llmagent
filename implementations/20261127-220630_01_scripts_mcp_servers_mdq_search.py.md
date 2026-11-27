## Goal

Build the MDQ search query from one boundary: the authorized-source predicate is applied in SQL before `COUNT`, ranking, and `LIMIT`; path and tag filters use exact comparison; failures are classified by cause against the closed code vocabulary; raw query text is removed from the response, metadata, and the persistent log line; each search owns its connection and is cancellable within a bounded drain (REQ-001, REQ-002, REQ-003, REQ-004, REQ-005).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan steps 2, 3, 4 cite this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- Companion test rows (SKILL.md conditions 1-4 hold; each is named only by this row and needs no design decision of its own): `tests/mcp_servers/mdq/test_search.py`, `tests/mcp_servers/mdq/test_mdq_search_counts.py`.
- `scripts/db/helper.py` is not modified; `SQLiteHelper` is consumed as it stands with a caller-supplied `db_path`.
- The closed code vocabulary and the hashed query identifier come from plan 001 (`scripts/mcp_servers/mdq/mdq_error_codes.py`, `scripts/mcp_servers/mdq/audit_target.py`); this document consumes them and defines none.
- Execution-order dependency on plan 001: its 19 procedures are still Pending. `tools/plan_dependency_order.py` reports this plan Ready on 20261127 because plan 001's generation cycle completed, so no Step 3c gated marker is written here.
- The canonicalized roots are exposed by `scripts/mcp_servers/mdq/auth.py` (seq 02); this document does not re-implement authorization.
- Stored `source_path` values are canonical (`path.resolve().as_posix()` at index time), so the SQL prefix predicate compares canonical values; the Python check stays as the last gate for symlink escapes.
- `json_each()` is available in both the development and production SQLite builds (3.53.4 and 3.53.1 verified); a `NULL` `tags_json` resolves to no rows rather than an error.
- The bounded active-search limit follows `DEFAULT_PER_SERVER_CONCURRENCY = 8`; no new configuration key is introduced. The bounded drain interval is a named constant in this module; its value is UNK-02.

## Design decisions
- One boundary builds the WHERE clause, so `COUNT`, ranking, and `LIMIT` all read the same predicate and cannot disagree about which rows are visible.
- Exact prefix comparison replaces `LIKE`, so wildcard characters in a user-supplied prefix cannot widen the result set.
- Cause-based classification replaces the generic `OperationalError` fallback, so a swallowed failure becomes a code from the closed vocabulary.
- The response and the log carry the hashed identifier, never the query text.

## Alternatives considered
- Keep the Python post-`LIMIT` authorization filter as the only gate — rejected: `matched_count` would still count unauthorized rows, which is the behavior REQ-002 removes.
- Keep the generic `OperationalError` branch and add a code mapping at the handler — rejected: the branch swallows the cause before the handler can classify it.

## Implementation
### Target file
`scripts/mcp_servers/mdq/search.py`

### Procedure
- Build the authorized-source predicate in SQL before `COUNT` (line 149), ranking, and `LIMIT` (line 159), from the canonicalized roots exposed by seq 02.
- Replace the `LIKE` predicates in `_build_search_where()` (lines 218, 222) with exact prefix comparison, and the tag predicate (line 227) with `json_each()` exact matching.
- Replace the generic `sqlite3.OperationalError` branch (line 192) with cause-based classification against the closed code vocabulary.
- Remove the raw query text from the response text, from `query_preview` (line 49), and from the persistent log line (line 133); use the hashed identifier.
- Give each search its own connection through `SQLiteHelper` instead of `service._get_db_connection()` (line 141), install the progress-handler stop event, and close in the worker's `finally` (line 202).
- Set the stop event on async timeout (line 51), wait for the worker inside the bounded drain interval, and refuse reuse of an interrupted connection.
- Apply the bounded active-search concurrency limit and the non-sensitive timeout and cancellation metrics.

### Method
- The predicate is built once and reused by the count query and the ranking query, so the count and the visible rows come from the same authorized set.
- The stop event is checked by the progress handler, which is the only place SQLite can interrupt an in-progress statement.
- Classification reads the exception cause, not the exception class name.

### Details
- `authorize_path()` (line 189) stays as the last gate for symlink escapes that a SQL prefix predicate cannot see.
- The header wording tests pin the truncation wording; the wording is unchanged, only the count source changes.

### Companion test files
- `tests/mcp_servers/mdq/test_search.py`
  - Procedure: replace `test_non_corruption_operational_error_returns_empty_results_without_raising` (line 120) with the cause-based classification expectation; add the wildcard-prefix, exact-tag, and no-raw-query-text tests.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_search.py`
- `tests/mcp_servers/mdq/test_mdq_search_counts.py`
  - Procedure: change `test_matched_count_is_exact_regardless_of_limit` (line 45) to the authorized-count expectation with an unauthorized row present; the header-wording tests stay unchanged.
  - Validation: `uv run pytest tests/mcp_servers/mdq/test_mdq_search_counts.py`

## Compatibility considerations
- The response shape keeps its fields; only the value of `query_preview` changes, so consumers that read it as an opaque string are unaffected.
- `tests/mcp_servers/mdq/test_mdq_search_modes.py` (seq 07) pins the request contract that must stay unchanged; this document does not change mode or cap behavior.

## Security considerations
- No raw query text may reach a persistent log or the response (AC-5).
- An unauthorized row must not change a visible count or fill a `LIMIT` slot (AC-1).

## Rollback considerations
- Revert the commit; the Phase 1 characterization tests in seq 07, 08, 10 fail again, which is the expected pre-change state.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_search.py tests/mcp_servers/mdq/test_mdq_search_counts.py tests/mcp_servers/mdq/test_mdq_search_limits.py tests/mcp_servers/mdq/test_mdq_search_modes.py tests/mcp_servers/mdq/test_mdq_read_authorization.py tests/mcp_servers/mdq/test_mdq_path_jail.py tests/mcp_servers/mdq/test_mdq_search_cancellation.py`
- Full sequence per `rules/toolchain.md`, including `uv run python tools/check_module_size.py` and `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `matched_count` is the authorized count.
- Path and tag filters use exact comparison.
- Every search failure resolves to a code from the closed vocabulary.
- No raw query text appears in the response, metadata, or persistent log.
- Each search owns its connection, is cancellable within the bounded drain, and an interrupted connection is not reused.

## Out of Scope
- The code vocabulary and the hashed identifier (plan 001).
- The canonicalized-root exposure (seq 02).
- The documentation of the query boundary (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Depends on plan 001 procedures (codes, hashed identifier), which are still Pending |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Companion test files are covered by this document |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Documentation is a separate row (seq 11) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-001 (query boundary), REQ-002 (authorized count and limit), REQ-003 (cause-based classification), REQ-004 (cancellation and concurrency), REQ-005 (no raw query text)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `scripts/mcp_servers/mdq/search.py`, `tests/mcp_servers/mdq/test_search.py`, `tests/mcp_servers/mdq/test_mdq_search_counts.py`
