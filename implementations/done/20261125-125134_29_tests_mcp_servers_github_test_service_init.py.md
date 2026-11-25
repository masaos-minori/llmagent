## Goal

Rewrite the client-initialization characterization for the config-built client (REQ-002; amended into the Plan as a fallout row).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Fallout amendment of 2026-11-25: the file pins the import-time `_gh` singleton at lines 31-63, which the init document removes.

## Design decisions

- Test-only change; behavior under test is defined by the code documents of the release unit.

## Alternatives considered

N/A: test-only row.

## Implementation
### Target file
`tests/mcp_servers/github/test_service_init.py`

### Procedure
Replace the module-reload cases with `build_client` cases.

### Method
- With an empty token `build_client` returns an unauthenticated client and logs the warning; with a token it is authenticated via `Auth.Token` and logs nothing.
- Assert the client's requester has the configured timeout and no retry for both cases.
- Assert `_GITHUB_TOKEN` is still read from the environment at import.

### Details
- Follow the existing fixture style of the file.

## Compatibility considerations

Test-only.

## Security considerations

N/A: test code.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/github/test_service_init.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- No test reads the removed `_gh` attribute.

## Out of Scope

- Production code (other documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test file described in Implementation > Procedure/Method/Details | Completed | 20261125-192517 | 20261125-192517 | module-reload cases already replaced by build_client cases during procedure 08; added the timeout/retry assertions to both the token and empty-token cases and the import-time environment read case |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261125-192517 | 20261125-192517 | ruff/mypy pass; 7 tests pass; no test reads the removed _gh attribute |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261119-140513_mcpai006_github-write-retry-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-124502_mcpai006_github-write-retry-policy.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-125134
- **Related target files**: `tests/mcp_servers/github/test_service_init.py`