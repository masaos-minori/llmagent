## Goal

Flip the assertion that pins silent ignoring of extra fields, and read `get_chunk`'s truncation state from metadata instead of the display marker (`REQ-001`, `REQ-004`, `AC-1`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

- `test_use_summary_field_silently_ignored` (method at line 80) becomes a rejection case.
- `test_get_chunk_truncates_large_content` (method at line 57, assertion at line 72) asserts the metadata pair instead of the `"[Truncated —"` marker.

## Assumptions

- With `extra="forbid"` plus `strict=True` on `GetChunkRequest` (row 01), constructing it with `use_summary=True` raises `pydantic.ValidationError`, so the flip is the requirement's intended behavior, not a regression: the module's docstring records that the field was removed and the old behavior was silent ignoring.
- The truncation state is the metadata read row 04 fills: `truncated`, `truncation_char_count`, `char_count`. The display marker may still appear, but no assertion here depends on it, which is what `AC-5` requires.
- `service.max_chars_per_chunk = 100` is set directly on the service instance in the existing test; the metadata reports the effective cap, so the fixture does not change.
- Module classification stays as it is: `tests/mcp_servers/mdq/` is not a classified area and the module carries no marker.
- `tests/mcp_servers/mdq/test_mdq_exception_handlers.py::TestGetChunkTruncationAuditDetail` is a verification dependency only; it still passes because the audit detail keeps the `truncated=true` part.

## Design decisions

- Assert the metadata field rather than keeping the marker assertion as an extra check: keeping both would pin formatter wording again, which is the coupling `AC-5` removes.

## Alternatives considered

- `N/A: the old behavior is a contract violation, so there is no characterization alternative to keep.`

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`

### Procedure
1. Rename `test_use_summary_field_silently_ignored` to a rejection case and assert `pytest.raises(ValidationError)` on `GetChunkRequest(chunk_id="x", use_summary=True)`; update its docstring and the class name `TestUseSummaryFieldRemoved` wording.
2. Unpack `result` into text and metadata in `test_get_chunk_truncates_large_content` and assert `metadata["truncated"] is True` with `truncation_char_count` set.

### Method

- Both changes are inside the existing classes and fixtures; no new fixture is needed.

### Details

- The class name `TestUseSummaryFieldRemoved` stays, since the requirement it records is the same one; only its single test changes.

## Compatibility considerations

- `N/A: test-only change; the assertions this module pins are the contract row 01 and row 04 implement.`

## Security considerations

- `N/A: test-only change.`

## Rollback considerations

- `N/A: revert the commit.`

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`
- `uv run python tools/check_test_taxonomy.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- An extra field on `get_chunk` is rejected, matching the Agent-side decision (`AC-1`).
- The truncation state is asserted through metadata, with no assertion depending on the display marker (`AC-4`, `AC-5`).

## Out of Scope

- The audit-detail read path (`scripts/mcp_servers/mdq/mdq_server.py`, row 03).
- The metadata shape definitions (`scripts/mcp_servers/mdq/mdq_models.py`, row 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Plan Phase 2 and Phase 4 (test assertions) |
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
- **Requirement ID**: REQ-001, REQ-004, AC-1, AC-4
- **Source issue**: `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-184702_mdqmcp008_mdq-schema-scope-consistency.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-084218
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_get_chunk_behavior.py`
