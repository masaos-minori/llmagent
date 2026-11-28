## Goal

Assert the machine-readable consistency state during an active refresh, and keep the display-wording check as a separate assertion (`REQ-003`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

- `test_is_indexing_warning_visible_during_active_index` (line 197) asserts `metadata["refresh_in_progress"] is True` as the consistency signal.
- One new test keeps the display wording pinned separately, so the module still records that the warning text appears.

## Assumptions

- The test already unpacks `text, _metadata` from `search_docs()`, so the pair is available at the assertion point; only the asserted source changes.
- `refresh_in_progress` is `self._is_indexing` (row 04), which the fixture sets by running `index_paths()` as a task and yielding once so the lock is acquired — the state is read during the real transition, not set by hand.
- `index_generation` is not asserted during the active refresh here, because no refresh has completed yet in this fixture; the completed-generation case lives in row 13.
- The existing `patch`/monkeypatch target is the origin module (`scripts/mcp_servers/mdq/mdq_service.py::_index_paths`), which `tools/check_mock_patch_targets.py` accepts, so no suppression comment is needed.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area and the module carries no marker.

## Design decisions

- Split the state assertion from the wording assertion into two tests, which is what makes `AC-5` checkable: the state test cannot pass by changing the wording, and the wording test cannot pass by changing the state.

## Alternatives considered

- `N/A: the current single assertion is the coupling this row removes.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_index_serialization.py`

### Procedure
1. In `test_is_indexing_warning_visible_during_active_index`, assert the metadata flag instead of the `"[WARNING: Index is being updated"` substring.
2. Add a test with the same fixture that asserts the warning substring appears in the returned display text.

### Method

- Both tests share the existing `service` and `md_file` fixtures and the slow-`_index_paths` monkeypatch.

### Details

- The renamed docstring of the first test should say it pins the reported state, not the wording, so the two tests read as state and display.

## Compatibility considerations

- `N/A: test-only change.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_index_serialization.py`
- `uv run python tools/check_mock_patch_targets.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The consistency state during an active refresh is asserted through metadata (`AC-4`).
- The display wording is asserted by a separate test, so a wording change cannot satisfy `AC-5` (`AC-5`).

## Out of Scope

- The read paths that fill the metadata (`scripts/mcp_servers/mdq/mdq_service.py`, row 04).
- The multi-read-path state case (`tests/mcp_servers/mdq/test_mdq_read_consistency_metadata.py`, row 13).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 4 |
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
- **Requirement ID**: REQ-003, AC-5
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_index_serialization.py`
