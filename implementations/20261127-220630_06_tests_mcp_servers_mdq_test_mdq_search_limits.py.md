## Goal

Assert that the `LIMIT` slots are filled only by authorized rows, so an unauthorized row cannot suppress an authorized result (REQ-002, AC-1).

## Scope
**Release unit**: query-boundary-characterization-tests (Plan step 1 cites this row; the unit covers Phases 1, 2, 3, 4)

## Assumptions
- This row keeps its own document because it fails the companion condition (2): no code row in this plan names it in its `Related Tests` cell.
- Written in Phase 1 before the production change; the added assertion fails first and pins the current post-`LIMIT` authorization order.
- The existing cap assertions stay unchanged; only the authorization order is added.
- Execution-order dependency on plan 001: its procedures are still Pending, so the Step 3c gated marker is written on each pending row of this document. `tools/plan_dependency_order.py` reports this plan Ready on 20261127 because plan 001's generation cycle completed; the marker records the substantive dependency, not tool readiness.

## Design decisions
- The test places an unauthorized row that ranks above an authorized row, so a `LIMIT` slot taken by the unauthorized row is observable as a missing authorized result.
- The assertion is on the returned rows, not on the internal authorization call.

## Alternatives considered
- Assert the authorization call order directly — rejected: the requirement is about the visible result set, and an internal-order assertion would pass even if the SQL predicate changed the order.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_search_limits.py`

### Procedure
- Add the case where an unauthorized row ranks above an authorized row and the `LIMIT` slots contain only authorized rows.
- Keep `test_default_limit_from_config` (line 44), `test_explicit_limit_below_cap_is_honored` (line 54), and `test_explicit_limit_above_cap_is_bounded_at_sql_layer` (line 66) unchanged.

### Method
- Rows are indexed under two roots and the allowlist is narrowed to one, so the unauthorized row is present in the database but not visible.

### Details
- The fixture uses the same service construction the existing tests use; no new fixture is introduced.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- This file is the AC-1 guard for the limit path.

## Rollback considerations
- N/A: revert the commit; the added test fails again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_search_limits.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- An unauthorized row cannot occupy a `LIMIT` slot.
- The cap behavior is unchanged.

## Out of Scope
- The SQL predicate (seq 01) and the canonicalized roots (seq 02).

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
- **Requirement ID**: REQ-002 (authorized `LIMIT` slots)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_search_limits.py`
