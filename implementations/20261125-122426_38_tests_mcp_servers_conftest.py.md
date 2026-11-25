## Goal

Emulate the preview-capability bootstrap seam in the shared autouse fixture (REQ-010; amended into the Plan as a fallout row), so endpoint tests that build server apps directly resolve previews like a live server.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Fallout amendment of 2026-11-25: the fixture configures dedup and the retry-policy map but not the preview map, so dry-run calls in endpoint tests would resolve to `applied`.
- All ten `TOOL_LIST` modules already named in this file carry `preview_capability`.

## Design decisions

- Reuse the existing `_TOOL_LIST_MODULES` and add one helper that returns the union of entries, so both maps are built from one source.

## Alternatives considered

A second fixture was rejected: the two seams must be configured together, as `run_http` does.

## Implementation
### Target file
`tests/mcp_servers/conftest.py`

### Procedure
Extend `_emulate_dedup_bootstrap` to configure and reset the preview map.

### Method
- Add `_declared_tool_entries` (new) taking `() -> list[dict]` returning every `TOOL_LIST` entry across `_TOOL_LIST_MODULES`; build `_declared_retry_policies` on top of it.
- In the fixture, call `configure_tool_preview_capabilities(_declared_tool_entries())` from `mcp_servers.execution_context` after the retry map is set.
- In teardown call `configure_tool_preview_capabilities(())`.

### Details
- Keep the logger-propagation fixture and the isolated-dedup fixture unchanged.

## Compatibility considerations

Test-only; an unconfigured test elsewhere keeps the safe default (`applied`).

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers -x -q`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Endpoint tests see the same preview resolution as a live server.
- Teardown leaves no preview configuration behind.

## Out of Scope

- New test cases (other documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `tests/mcp_servers/conftest.py`
