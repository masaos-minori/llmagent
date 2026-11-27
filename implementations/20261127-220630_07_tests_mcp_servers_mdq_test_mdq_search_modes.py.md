## Goal

Keep the mode and cap characterization passing under the new query boundary and add the genuine zero-result case (REQ-003, AC-3).

## Scope
**Release unit**: query-boundary-characterization-tests (the unit covers Phases 1, 2, 3, 4; this row is covered by the plan's Tests section, not by an `Implementation steps` entry)

## Assumptions
- Plan Gap recorded by this pass: no `Implementation steps` entry cites this row; the row is covered by the plan's Tests section (REQ-003), not by a step.
- This row keeps its own document because it fails the companion condition (2): no code row in this plan names it in its `Related Tests` cell.
- Written in Phase 1 before the production change; the zero-result assertion fails first because the current boundary reports a count for rows the caller cannot see.
- Execution-order dependency on plan 001: its procedures are still Pending, so the Step 3c gated marker is written on each pending row of this document. `tools/plan_dependency_order.py` reports this plan Ready on 20261127 because plan 001's generation cycle completed; the marker records the substantive dependency, not tool readiness.

## Design decisions
- The mode and cap assertions are behavior locks: they must not change under the new boundary, so the document adds no new mode behavior.
- The genuine zero-result case is a query that matches rows only outside the authorized roots, so the count is zero for the caller.

## Alternatives considered
- Treat the existing zero-match test as sufficient — rejected: it matches nothing at all, so it cannot show that an authorized-only count differs from a database-wide count.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_search_modes.py`

### Procedure
- Keep `test_default_mode_is_bm25` (line 37), `test_unsupported_mode_rejected` (line 45), and `test_request_override_above_cap_is_bounded` (line 100) unchanged.
- Add the genuine zero-result case: rows exist in the index, all outside the authorized roots, and the caller sees zero matches.

### Method
- The fixture indexes under one root and authorizes a different root, so the rows exist but are not visible.

### Details
- The assertion is on `matched_count` and on the returned rows together, so a count that disagrees with the visible rows is caught.

## Compatibility considerations
- N/A: test-only change.

## Security considerations
- AC-3 is the requirement this file guards: a genuine zero result must be distinguishable from a filtered result.

## Rollback considerations
- N/A: revert the commit; the added test fails again.

## Validation plan
- `uv run pytest tests/mcp_servers/mdq/test_mdq_search_modes.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria
- The mode and cap behavior is unchanged.
- A query whose matches are all outside the authorized roots reports zero for the caller.

## Out of Scope
- The SQL predicate (seq 01).
- The documentation of filter semantics (seq 11).

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
- **Requirement ID**: REQ-003 (genuine zero-result case, AC-3)
- **Workflow phase**: plan-to-implementation-procedure
- **Source issue**: `issues/done/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-161505_mdqmcp002_mdq-search-query-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-220630
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_search_modes.py`
