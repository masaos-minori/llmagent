## Goal

Create the cancellation and concurrency tests: dedicated connection per search, stop event on timeout, bounded drain, no reuse of an interrupted connection, bounded concurrency, and the repeated-timeout resource-leak test (REQ-004, AC-4).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- This row keeps its own document because it fails the companion condition (3): the cancellation, drain, and connection-lifecycle assertions are design decisions of this row, not assertion updates following a boundary another row decides.
- The file does not exist yet; `tests/mcp_servers/mdq/` holds 35 test files and none covers cancellation or worker leakage.
- Written in Phase 1 before the production change; the tests fail first and pin the current behavior, where the worker is not interrupted and the connection is shared.
- Execution-order dependency on plan 001: its procedures are still Pending, so the Step 3c gated marker is written on each pending row of this document. `tools/plan_dependency_order.py` reports this plan Ready on 20261127 because plan 001's generation cycle completed; the marker records the substantive dependency, not tool readiness.

## Design decisions
- The leak test runs the timeout path repeatedly and asserts the connection count returns to the baseline, so a single leaked connection is observable.
- The no-reuse assertion is on the connection object identity, not on a counter, so reuse of an interrupted connection is caught even when the count looks correct.
- The bounded-drain assertion measures the wait against the named constant, so a worker that never stops is caught.

## Alternatives considered
- Assert only that the timeout raises — rejected: AC-4 requires the resource lifecycle, which a raise assertion cannot show.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_search_cancellation.py` (new)

### Procedure
- Add the dedicated-connection-per-search test.
- Add the stop-event-on-timeout test and the bounded-drain test.
- Add the no-reuse-of-an-interrupted-connection test.
- Add the bounded-concurrency test at the documented per-server limit.
- Add the repeated-timeout resource-leak test.

### Method
- Connections are counted through `scripts/db/helper.py` as it stands, with a caller-supplied `db_path`; the helper is not modified.
- The progress-handler stop event is triggered by the test, so the interruption is observable without waiting for a real long query.

### Details
- The tests are marked with the plan's test-taxonomy marker used by the other MDQ test modules.

## Compatibility considerations
- N/A: new test file.

## Security considerations
- The timeout and cancellation metrics must be non-sensitive: no query text, no absolute path (AC-4).

## Rollback considerations
- N/A: revert the commit; the file stays as the characterization record.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_search_cancellation.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- Each search owns its connection and closes it in the worker's `finally`.
- A timed-out search stops within the bounded drain and its connection is not reused.
- Concurrency stays at the documented limit, and no connection leaks across repeated timeouts.

## Out of Scope
- The cancellation implementation (seq 01).
- The documentation of cancellation behavior (seq 11).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there | Depends on plan 001 procedures, which are still Pending |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: plans/20261127-160114_mdqmcp001_mdq-server-boundary.md phase all - the closed error-code vocabulary and the single audit-emission boundary this plan's classification and metrics must match are defined there |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Requirement ID**: REQ-004 (cancellation, connection lifecycle, bounded concurrency, non-sensitive metrics)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_search_cancellation.py`
