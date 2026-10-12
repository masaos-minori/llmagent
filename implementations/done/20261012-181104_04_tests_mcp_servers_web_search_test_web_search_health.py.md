## Goal
- Pin the loopback health admission at the middleware level (admitted, rejected, unchanged elsewhere) and pin which servers opt in (`REQ-002`, `REQ-003`, `REQ-004`).

## Scope
- Only `tests/mcp_servers/web_search/test_web_search_health.py`: new test classes. Existing tests are not edited.

## Assumptions
- The framework test client accepts an explicit client address pair, so the loopback and non-loopback cases can be exercised; its default client host is the string testclient, which stands for a missing or unparsable address.
- The existing module already imports the test client, `health`, and `web_search_server`; the autouse reset fixture still applies and is harmless.

## Design decisions
- Build a fresh minimal FastAPI app per case with the real `attach_auth_middleware` (a health route and a protected route), rather than the real web-search app, whose token is read from configuration at import time.
- Assert the opt-in wiring by parsing the server source files with the standard syntax-tree module: the web-search call passes the keyword as the constant true, and the git, rag-pipeline, cicd, and mdq callers do not pass it.

## Alternatives considered
- Reloading the web-search module with a patched middleware to observe the argument: rejected, it risks leaking module-level state into other tests.

## Implementation
### Target file
`tests/mcp_servers/web_search/test_web_search_health.py`

### Procedure
1. Add the imports needed (`attach_auth_middleware` from the server module, FastAPI, the standard syntax-tree module, and `Path`) next to the existing imports.
2. Add a helper that builds a minimal app with a health route, a protected route, and the real middleware with the token browser-secret and the switch given as a parameter.
3. Add a new class for the middleware behavior with these tests, each using the test client with an explicit client address pair:
   - test_loopback_health_is_admitted_without_token (switch on, 127.0.0.1): 200.
   - test_loopback_health_is_admitted_with_the_main_token (switch on, header Bearer main-secret): 200.
   - test_loopback_ipv6_health_is_admitted (switch on, ::1): 200.
   - test_non_loopback_health_without_token_is_rejected and test_non_loopback_health_with_wrong_token_is_rejected (switch on, a documentation-range address): 401; and with the correct token: 200.
   - test_default_keeps_loopback_health_strict (switch off, 127.0.0.1, no token): 401.
   - test_protected_route_requires_token_even_on_loopback (switch on, 127.0.0.1): 401 without the token and 200 with it.
   - test_other_paths_are_not_exempt: switch on, loopback, paths that differ from the exact health path by a suffix or trailing slash: 401.
   - test_unparsable_client_address_is_not_loopback: the default test client (host testclient), switch on, no token: 401.
4. Add a new class for the wiring with two tests that read the server source files under the scripts directory (resolved relative to this test file) and parse them: test_web_search_server_opts_in finds the call to `attach_auth_middleware` and asserts it has the keyword exempt_health_on_loopback with the constant true; test_other_servers_do_not_opt_in is parametrized over the git, rag-pipeline, cicd, and mdq server files and asserts their call has no such keyword.
5. Run the new tests against the unmodified server module and confirm the exemption cases and the opt-in test fail while the strictness cases pass.

### Method
- Plain test functions grouped by class; keep the existing autouse fixture untouched.

### Details
- Use test names exactly as above (plain, not backticked); do not modify existing tests.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: fixed test strings only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/web_search/test_web_search_health.py -q`; before procedures 01 and 02 the admission and opt-in cases fail and the strictness cases pass; after them all pass.
- `uv run ruff format --check` and `uv run ruff check` on the file.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05 and 06 (documentation); the new tests must be seen failing before the code is edited.

## Completion criteria
- The tests exist and map to the plan's acceptance criteria; they fail before procedures 01 and 02 where expected and pass after; existing tests pass.

## Out of scope
- The end-to-end poll test (procedure 03) and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the middleware and opt-in wiring tests | Completed | 20261012-182000 | 20261012-182000 | stale_detector clean; changed: tests/mcp_servers/web_search/test_web_search_health.py (TestLoopbackHealthExemption, TestHealthExemptionOptIn; 17 new cases; those passing the keyword failed before the code, strictness-by-default cases passed) |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-182000 | 20261012-182000 | ruff pass; file passes |

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
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-004`
- **Source issue**: issues/done/20261012-173750_mcp004_web_search-mcp-server-startup-health-check-fails-due-to-browser_auth_token-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-181104
- **Related target files**: tests/mcp_servers/web_search/test_web_search_health.py