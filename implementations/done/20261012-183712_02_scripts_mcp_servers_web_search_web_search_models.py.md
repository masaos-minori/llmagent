## Goal
- Load the shared auth_token in the web-search config, remove the browser token and the unused token field of the browser config, and reject a configuration that still has the removed key (`REQ-001, REQ-002`)

## Scope
- `WebSearchConfig` (field, loading, and its docstring), `BrowserConfig` and its projection in `scripts/mcp_servers/web_search/web_search_models.py`.

## Assumptions
- Procedures 05 and 06 (tests) and 01 (config) are applied around this change.
- `BrowserConfig.auth_token` is never read (verified by search): only a test helper and the projection construct it.
- The helper `get_str` returns an empty string for an absent or null key and resolves environment references.

## Design decisions
- Mirror the git model: load the key with `get_str` and no default argument semantics beyond empty.
- Fail closed on the removed key: if the dictionary contains browser_auth_token, raise `ValueError` before any other parsing, with a message naming auth_token as the replacement.
- An empty token keeps the middleware's accept-all fallback, the same as the other servers.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`scripts/mcp_servers/web_search/web_search_models.py`

### Procedure
1. In the `WebSearchConfig` field list, remove the browser_auth_token field and add a string field auth_token with default empty.
2. At the start of `from_dict`, raise `ValueError` if the key browser_auth_token is present in the dictionary; the message names the removed key and says to use auth_token, shared with the agent configuration's web-search auth_token.
3. Replace the line that loads the browser token with a line that loads auth_token through `get_str`, and pass auth_token to the constructor instead of the browser token.
4. Update the `from_dict` docstring's Raises section to list the removed-key error.
5. In `BrowserConfig`, remove the auth_token field; in `from_web_search_config`, drop the fourth projected value and update its docstring from four fields to three.

### Method
- Edit only these places; keep annotations and the module's style; keep the noqa comments on the neighboring lines.

### Details
- The positional order of the remaining `BrowserConfig` fields is unchanged.
- Do not change `WebSearchConfig.load` or the other settings.

## Compatibility considerations
Breaking only for a configuration that still carries the removed key, which is the intent; every other setting loads as before.

## Security considerations
Fail-closed handling of a stale security setting: the removed key raises instead of leaving authentication disabled.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search -q`.
- `uv run ruff format --check` and `uv run ruff check` on the file, `uv run mypy --no-namespace-packages scripts/mcp_servers/web_search/web_search_models.py`, `uv run bandit -q -c pyproject.toml scripts/mcp_servers/web_search/web_search_models.py`, and `uv run lint-imports`.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The config exposes auth_token, the removed key raises, `BrowserConfig` has three fields, and the web-search tests pass.

## Out of scope
- The server wiring (procedure 03) and the other servers' models.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the browser token with auth_token in the config model and reject the removed key | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; changed: scripts/mcp_servers/web_search/web_search_models.py (auth_token field, removed-key ValueError, BrowserConfig without the token) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-184531 | 20261012-184531 | ruff, mypy --no-namespace-packages, bandit, lint-imports pass |

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
- **Requirement ID**: `REQ-001, REQ-002`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: scripts/mcp_servers/web_search/web_search_models.py