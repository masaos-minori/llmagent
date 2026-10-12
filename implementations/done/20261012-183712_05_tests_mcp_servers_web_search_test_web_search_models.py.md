## Goal
- Update the config tests for auth_token and add the removed-key error test (`REQ-002, REQ-004`)

## Scope
- `TestWebSearchConfigBrowserFields` and `TestBrowserConfig` in `tests/mcp_servers/web_search/test_web_search_models.py`, plus one new test.

## Assumptions
- The existing tests assert the browser token field; those assertions change to the new field.
- Environment references resolve through the helper, so a literal value is used in the dictionaries.

## Design decisions
- Keep each existing test's intent (defaults, loading, null handling, projection) and swap the field; add one test for the error.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_models.py`

### Procedure
1. In the defaults test and the from-dict defaults test, assert the new field is empty instead of the browser token.
2. In the custom-values test, pass auth_token with a literal value in the dictionary and assert it is loaded.
3. In the null-values test, pass a null auth_token and assert the field is empty.
4. In `TestBrowserConfig`, remove the token from the dictionary and the final assertion on the browser config's token (the field is gone).
5. Add test_removed_browser_token_key_raises: a dictionary containing browser_auth_token raises `ValueError`, and the message contains auth_token.
6. Run the tests against the unmodified model and confirm they fail (missing field, no error) before procedure 02.

### Method
- Follow the file's style: plain methods in the existing classes; use `pytest.raises` with a match string.

### Details
- Rename nothing else; the class names stay.

## Compatibility considerations
Test-only change.

## Security considerations
N/A: no input handling, credentials, or trust boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_models.py -q`; `uv run ruff format --check tests/mcp_servers/web_search/test_web_search_models.py` and `uv run ruff check tests/mcp_servers/web_search/test_web_search_models.py`.
- Execution order for the whole plan: tests first (procedures 05, 06, 07, 08, 09, 04), then the code (01, 02, 03), then the documentation (10 to 15); the new tests must be seen failing before the code is edited.

## Completion criteria
- The tests assert the new field and the error, fail before procedure 02, and pass after it.

## Out of scope
- Provider and health tests (procedures 06 and 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the config tests and add the removed-key test | Completed | 20261012-184531 | 20261012-184531 | stale_detector clean; tests first. changed: tests/mcp_servers/web_search/test_web_search_models.py (auth_token assertions, removed-key test); 10 tests failed together with procedure 06 before the model change |
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
- **Requirement ID**: `REQ-002, REQ-004`
- **Source issue**: issues/done/20261012-182600_mcp005_web-search-tool-calls-return-401-when-browser_auth_token-differs-from-auth_token.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-183348_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-183712
- **Related target files**: tests/mcp_servers/web_search/test_web_search_models.py