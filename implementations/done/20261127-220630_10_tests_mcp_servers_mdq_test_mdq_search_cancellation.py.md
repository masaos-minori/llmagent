## Goal

Create the cancellation and concurrency tests: dedicated connection per search, stop event on timeout, bounded drain, no reuse of an interrupted connection, bounded concurrency, and the repeated-timeout resource-leak test (REQ-004, AC-4).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- This row keeps its own document because it fails the companion condition (3): the cancellation, drain, and connection-lifecycle assertions are design decisions of this row, not assertion updates following a boundary another row decides.
- The file does not exist yet; `tests/mcp_servers/mdq/` holds 35 test files and none covers cancellation or worker leakage.
- Corrected 20261128: the directory holds 38 `test_*.py` modules (re-counted against current source); the none-covers-cancellation claim still holds.
- Corrected 20261128: the taxonomy claim does not apply as written. `tools/check_test_taxonomy.py` classifies modules under `tests/agent` and `tests/shared` only, and no MDQ module carries `pytestmark` today; plan 010 adds the marker to the five shared MDQ modules. This module carries the requirement citation (`REQ-004` plus the source issue path) in its docstring and no `pytestmark`, which is what the rule requires of a contract module once the marker is added later.
- Corrected 20261128: the bounded-drain assertion cannot be observed through the current call path, where the caller returns at the timeout without waiting for the worker; the test pins the post-change behavior. Because the helper's default `check_every` is 1000 VM steps, a short statement can finish before the stop event is observed, so the test uses a statement long enough for the progress handler to fire.
- Written in Phase 1 before the production change; the tests fail first and pin the current behavior, where the worker is not interrupted and the connection is shared.
- Execution-order dependency on plan 001: resolved 20261128 - its procedures have been executed and archived; the gated markers this document carried were cleared by owner decision on 20261128 (recorded in Execution Status Notes). `tools/plan_dependency_order.py` reports this plan Ready.

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
- Corrected 20261128: the helper exposes no connection counter, so counting is done by the test itself (monkeypatched `sqlite3.connect` recording each opened connection, plus the connection object identity), not by a helper facility. The helper is still not modified.
- The progress-handler stop event is triggered by the test, so the interruption is observable without waiting for a real long query.

### Details
- The tests carry the `REQ-004` citation and the source issue path in the module docstring; no `pytestmark` is added (see the 20261128 correction in Assumptions).

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261128-124000 | Gated marker cleared 20261128 by owner decision: the blocking plan plans/20261127-160114_mdqmcp001_mdq-server-boundary.md was executed and archived and plan_dependency_order.py reports this plan Ready - Depends on plan 001 procedures, which have landed and are archived Red-first confirmed 20261128: 6 red - helper ownership (search uses service accessor today), handler not installed, caller returns at timeout without waiting for a worker that never stops, interrupted connection not closed at raise, no active-search limit constant, peak exceeds limit; 2 guards pass today (connection-per-search identity, leak-at-raise observable) via a recording sqlite3.Connection stand-in |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261128-134500 | 20261128-134500 | All six reds green after the seq 01 implementation; three test adjustments recorded (drain measured inside the loop, follow-up search shortened to complete inside the timeout, gather with return_exceptions); member run 6 passed; gates clean; full suite once at end of unit, baseline-only failures. |

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
