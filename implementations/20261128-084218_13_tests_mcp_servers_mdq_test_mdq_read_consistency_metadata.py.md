## Goal

Assert that each MDQ read path reports its consistency state as metadata while a refresh is in progress, so the reported state does not depend on output wording (`REQ-003`, `REQ-004`, `AC-4`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

- New module, contract-classified (`pytestmark = pytest.mark.contract`, `REQ-003` and `REQ-004` citations in the docstring).
- One case per read path: `search_docs`, `outline`, `get_chunk`, `grep_docs`, `stats`.
- No display-wording assertion in this module; the wording case lives in `tests/mcp_servers/mdq/test_mdq_index_serialization.py` (row 10).

## Assumptions

- The state is read during the real transition, using the pattern row 10's module already uses: run `index_paths()` as a task and yield once so the lock is acquired and `_is_indexing` is True (`scripts/mcp_servers/mdq/mdq_service.py:285,298`).
- `index_generation` is None before the first completed refresh and increments at each completed refresh (Plan UNK-05 plan default); the during-refresh cases assert the value the read is looking at, not a post-refresh value.
- The fixtures are local to the module (`service`, `md_file`), the same pattern `test_mdq_service.py` and `test_mdq_index_serialization.py` use; no `conftest.py` exists for `tests/mcp_servers/mdq/`, so nothing is added there.
- `get_chunk` needs an indexed chunk before the read, so the module indexes once and reads the stored `chunk_id` through the service's own connection, as the existing truncation test does.
- Phase 1 pins the current signal as the warning string and the truncation marker; Phase 4 replaces those pins with the metadata assertions recorded here.

## Design decisions

- Assert only metadata in this module. Keeping the wording out is what makes `AC-5` testable: the module cannot pass by matching a string.
- One test per read path rather than a shared loop, so a path that fails to report the state is attributable to a named case.

## Alternatives considered

- Set `service._is_indexing = True` directly: rejected, it does not exercise the transition and would pass even if the read path computed the flag separately from the lock.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py` (new)

### Procedure
1. Add the `service` and `md_file` fixtures following the existing local pattern.
2. Add one async case per read path that holds the refresh open and asserts `refresh_in_progress` is True and `index_generation` is present in the returned metadata.
3. Add one post-refresh case that asserts `refresh_in_progress` is False and `index_generation` advanced after a completed refresh.
4. Add the `get_chunk` truncation case asserting `truncated`, `truncation_char_count`, and `char_count` from metadata.

### Method

- Each case unpacks the `(text, metadata)` pair the read paths return, so the asserted object is the metadata, and the text element is unused in the assertions.

### Details

- The metadata field names are the shapes row 01 declares: `SearchDocsMetadata`, `OutlineMetadata` (new), `StatsMetadata` (new), `GetChunkMetadata` (new), `GrepDocsMetadata`, `IndexPathsMetadata`.
- The stale-document case for `outline` reads the metadata pair through `tests/mcp_servers/mdq/test_mdq_outline_stale_helper.py` (row 17), so this module does not duplicate the stale boundary fixture.

## Compatibility considerations

- New module; no existing test is affected. `tests/mcp_servers/mdq/` is not a classified area, so the marker is checked only for citation and registration.

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`, including the diff-scoped coverage gate at the `rules/toolchain.md` threshold.

## Completion criteria

- Every read result produced during a refresh carries `refresh_in_progress` and `index_generation` (`AC-4`).
- `get_chunk` reports its truncation state in metadata (`AC-4`), and no assertion in this module depends on output wording (`AC-5`).

## Out of Scope

- The display-wording case (`tests/mcp_servers/mdq/test_mdq_index_serialization.py`, row 10).
- The read paths that fill the metadata (`scripts/mcp_servers/mdq/mdq_service.py`, row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 1 (pin) and Phase 4 (metadata assertions) |
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
- **Requirement ID**: REQ-003, REQ-004, AC-4, AC-5
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`
