## Goal
- Drop the token argument from the browser config helper (`REQ-002`)

## Scope
- The helper `_make_browser_config` in `tests/mcp_servers/web_search/test_web_search_provider.py`.

## Assumptions
- Only this helper constructs `BrowserConfig` in this file (verified by search).

## Design decisions
- Remove the argument so the helper matches the three-field config.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_provider.py`

### Procedure
1. In `_make_browser_config`, delete the auth_token keyword argument from the `BrowserConfig` construction.
2. Run the file against the unmodified model and confirm it fails with an unexpected-argument error before procedure 02.

### Method
- A one-line edit.

### Details
- Do not change the helper's signature or other tests.

## Compatibility considerations
Test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_provider.py -q`; `uv run ruff format --check tests/mcp_servers/web_search/test_web_search_provider.py` and `uv run ruff check tests/mcp_servers/web_search/test_web_search_provider.py`.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The helper builds a three-field config and the provider tests pass after procedure 02.

## Out of scope
- Other provider tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Drop the token argument from the helper | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: tests/mcp_servers/web_search/test_web_search_provider.py (helper drops the token argument) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-184531 | 20261012-184531 | ruff pass; file passes |

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
- **Requirement ID**: `REQ-002`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: tests/mcp_servers/web_search/test_web_search_provider.py