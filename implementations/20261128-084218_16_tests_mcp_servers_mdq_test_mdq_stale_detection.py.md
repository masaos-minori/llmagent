## Goal

Assert the outline consistency state through metadata instead of the warning text in the returned value, now that `outline()` returns a text-plus-metadata pair (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

- Line 89: the absence case asserts the metadata state is not stale.
- Line 118: the presence case asserts the metadata state is stale.

## Assumptions

- `OutlineMetadata` carries the stale state (`stale: bool`) alongside `refresh_in_progress` and `index_generation`, per the Plan's Design statement that the display wording is kept and the state moves to metadata. Row 01 is the row that owns the metadata shapes; the recorded requirement text names only the two consistency fields, so the stale field is the reading these two amended rows depend on and is reported for confirmation.
- The mtime fixture is unchanged: the test writes `mtime_ns` through the service connection so the predicate sees a document one nanosecond past the boundary.
- The docstring wording "must still be flagged" stays accurate once the assertion reads the state; no other assertion in the module reads outline's returned text, except the module's `is_stale`/`STALE_SQL_CONDITION` agreement cases, which call the predicate directly.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area and the module carries no marker.

## Design decisions

- Assert the state, not the wording, which is what makes `AC-5` checkable from this module.

## Alternatives considered

- Unpack the pair and keep the substring assertions on the text element: rejected, that leaves the assertion satisfied only by display wording, which `AC-5` excludes.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_stale_detection.py`

### Procedure
1. Unpack the returned pair in the two outline cases and assert the metadata state at lines 91 and 118.
2. Keep the predicate and SQL-condition agreement cases as they are.

### Method

- The cases keep the same fixture and the same boundary construction; only the asserted object changes.

### Details

- The absence case asserts `metadata["stale"] is False`; the presence case asserts `metadata["stale"] is True`.

## Compatibility considerations

- `N/A: test-only change.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_stale_detection.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The outline consistency state is asserted through metadata (`AC-4`, `AC-5`).

## Out of Scope

- The metadata shape definition (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).
- The read path that fills it (`scripts/mcp_servers/mdq/mdq_service.py`, row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 4 (amendment 2026-11-28) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_stale_detection.py`
