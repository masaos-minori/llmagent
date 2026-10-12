## Goal
- Prove through the real health poll that a web-search-style server whose middleware expects a distinct token becomes healthy over loopback once the switch is on, that the poll sends the main token, and that the same server without the switch is still not healthy (`REQ-001`, `REQ-003`).

## Scope
- Only `tests/agent/test_http_lifecycle_health_check.py`: one new test class and small module-level helpers. Existing tests are not edited.

## Assumptions
- The poll builds its own HTTP client inside `_health_poll_until_ready` with the main token in the default headers, so the test replaces `AsyncClient` in the module (as the existing tests do) with a factory that returns a real client bound to an in-process ASGI transport.
- The ASGI transport reports the client address as loopback by default, which stands in for the agent polling over 127.0.0.1.
- The module's poll-interval constant can be patched to a small value so the failure case ends quickly.

## Design decisions
- Test end to end through the real middleware (`attach_auth_middleware` from the server module) on a minimal app, rather than mocking the response, so a regression in either side fails.
- Record the Authorization header the app receives to assert the main token is what the poll sends.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_health_check.py`

### Procedure
1. Add the imports needed (the HTTP client module, FastAPI, and `attach_auth_middleware` from the server module) next to the existing imports, and a time import if not already present.
2. Add a small helper that builds a minimal FastAPI app with a health route returning a healthy JSON body and recording the Authorization header it received into a list, attaches `attach_auth_middleware` with the browser token browser-secret and the switch given as a parameter, and returns the app and the list.
3. Add a helper that returns a client factory: a function that accepts the same keyword arguments the poll passes (timeout and headers) and returns a real async HTTP client built with those arguments over an ASGI transport for the given app.
4. Add a new test class with three async tests, using the existing `_make_cfg` helper with the main token main-secret and the existing manager fixture:
   - test_poll_succeeds_when_switch_on_and_tokens_differ: patch the module's `AsyncClient` with the factory, patch the poll interval to a small value, run `_health_poll_until_ready` with a deadline a few seconds ahead; expect it returns without raising, and the recorded header equals Bearer main-secret.
   - test_poll_fails_when_switch_off_and_tokens_differ: same with the switch off and a short deadline; patch `_cleanup_server_resources` and the process terminator as the existing tests do; expect `HttpStartupError`.
   - test_poll_succeeds_when_tokens_match_and_switch_off: the middleware token equals the main token and the switch is off; expect success (the unchanged behavior of the other servers).
5. Run the new tests against the unmodified server module and confirm the first fails (the keyword is not yet accepted, or the poll is refused) while the other two behave as described.

### Method
- Follow the file's style: async tests marked for pytest-asyncio, the `mgr` fixture, patching with `patch.object` on the module.

### Details
- Keep the deadlines small so a failing case does not slow the suite.
- Do not modify existing tests.

## Compatibility considerations
N/A: test-only change.

## Security considerations
N/A: no secrets; the tokens are fixed test strings.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py -q`; before procedure 01 the switch-on test fails; after it all pass with the existing tests.
- `uv run ruff format --check` and `uv run ruff check` on the file.
- Execution order for the whole plan: procedures 03 and 04 (tests) first, then 01 and 02 (code), then 05 and 06 (documentation); the new tests must be seen failing before the code is edited.

## Completion criteria
- The three tests exist; the switch-on test fails before procedure 01 and passes after; the other two pass in both states; existing tests are unchanged and pass.

## Out of scope
- Testing the real web-search app wiring (procedure 04) and the docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the end-to-end health poll tests | Completed | 20261012-182000 | 20261012-182000 | stale_detector clean; changed: tests/agent/test_http_lifecycle_health_check.py (TestStartupPollWithDistinctServerToken, 3 tests). Corrected during implementation: the factory captures the real AsyncClient before patching (patching replaces the shared httpx attribute), and the helper passes the keyword only when enabling it so the off-cases pin the old call shape; only the switch-on test failed before the code |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched file | Completed | 20261012-182000 | 20261012-182000 | ruff pass; 8 tests in the file pass |

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
- **Requirement ID**: `REQ-001`, `REQ-003`
- **Source issue**: issues/done/20261012-173750_mcp004_web_search-mcp-server-startup-health-check-fails-due-to-browser_auth_token-mismatch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261012-175600_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-181104
- **Related target files**: tests/agent/test_http_lifecycle_health_check.py