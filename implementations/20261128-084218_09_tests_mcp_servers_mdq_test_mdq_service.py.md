## Goal

Drop the assertion for the removed field and read the service read paths' consistency state from metadata, so the module tests the pair the read paths return (`REQ-003`, `REQ-005`, `AC-4`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

- `test_get_chunk_request_defaults` (method at line 260) loses
  `assert req.with_neighbors is False` (line 260).
- The read-path assertions that treat the returned value as text unpack the pair: `test_get_chunk_returns_content_after_indexing` (784), `test_stats_returns_counts_after_indexing` (858), `test_stats_includes_fts_count` (869), `test_stats_includes_stale_count` (875), `test_outline_returns_headings` (938), `test_outline_truncates_large_heading_list` (1006), `test_request_override_bounded_by_config_cap` (1020).
- One new assertion per read path for the post-refresh consistency state.

## Assumptions

- The text assertions stay as they are after unpacking: the display wording is unchanged, only the returned shape is a pair.
- After a completed refresh the state is `refresh_in_progress` False with `index_generation` set, which is what the post-refresh assertions check; the during-refresh case belongs to row 13 and is not duplicated here.
- `grep_docs` and `index_paths` assertions in this module already unpack the pair (they return it today), so they need no shape change.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area and the module carries no marker.
- `test_search_timeout_raises_mdq_consistency_error` and `test_get_chunk_not_found` call the read paths only inside exception assertions, so they are verification dependencies.

## Design decisions

- Check the state through metadata in the existing tests rather than creating a parallel set of tests: the read paths already own these fixtures, and a second set would double the fixture cost for the same fact.

## Alternatives considered

- `N/A: the return-shape change requires unpacking, so there is no alternative that keeps these assertions unchanged.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_service.py`

### Procedure
1. Remove the `with_neighbors` assertion.
2. Unpack the pair in the seven read-path assertions named in Scope and keep the text assertions on the text element.
3. Add one assertion per read path that the metadata carries `refresh_in_progress` and `index_generation` after a completed refresh.

### Method

- The unpacking uses `text, metadata = asyncio.run(...)`, the form this module already uses for `index_paths` and `grep_docs`.

### Details

- `test_outline_truncates_large_heading_list` and `test_request_override_bounded_by_config_cap` assert display wording ("Truncated", "headings found"); those stay on the text element, which is what keeps them display tests rather than state tests.

## Compatibility considerations

- `N/A: test-only change.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_service.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- No assertion references `with_neighbors` (`REQ-005`).
- Each read path's consistency state is asserted through metadata, with display-wording assertions kept separate (`AC-4`, `AC-5`).

## Out of Scope

- The during-refresh consistency case (`tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`, row 13).
- The read paths that fill the metadata (`scripts/mcp_servers/mdq/mdq_service.py`, row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 (REQ-005) and Phase 4 (REQ-003) |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-003, REQ-005, AC-4, AC-5
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_service.py`
