## Goal

Create the runtime-enforcement contract tests at `POST /v1/call_tool` (REQ-001, REQ-002, AC-1,
AC-2, AC-4): the authorization, validation, and dedup decisions are observed through the real
HTTP boundary with only the GitHub API client mocked.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The behaviors under test are already implemented (Plan Step 2 evidence), so the tests are
  expected to pass; a failure is a behavior gap reported against the owning issue (REQ-005), not
  fixed here.
- Domain exceptions reach the transport handlers (`scripts/mcp_servers/github/exception_handlers.py`),
  so the observable contract is the HTTP status: 403 authorization, 401 unauthenticated.
- The root conftest sets `MCP_GITHUB_AUTH_TOKEN` (`tests/conftest.py:338-345`), so the server module
  imports; the fixture named here is the one row 1 creates.

Step 3b corrections (20261126, verified against current source):

1. Validation failures do not reach the transport handler. `GitHubValidationError` is a `ValueError`
   subclass (`github_models_config.py:196`) and `dispatch_tool` catches `ValueError` at
   `scripts/mcp_servers/dispatch.py:486-498`, converting it into an error result. So at the HTTP
   boundary a validation failure is `200` with `is_error: true`, not 400; only the `RuntimeError`-based
   domain errors (authorization, `github_models_config.py:188`) propagate to
   `exception_handlers.py:34` and produce 403. The validation cases below assert the boundary result,
   not a 400 status.
2. Line citations: `_resolve_search_query` is at `github_service_security.py:267` (271-273 is its
   docstring); the read-size enforcement is `_assert_max_read_file_size` at
   `github_service_security.py:156` — line 456 is the security-posture reporting branch, not the
   guard. In `github_service_file.py` the size guard call is line 55 and the decode is 57-61.
3. The disabled-tool gate at `github_server.py:244-247` runs before dispatch and returns
   `Tool disabled` when `_GITHUB_TOKEN` is empty, which is the test environment's state, so the test
   patches `_GITHUB_TOKEN` non-empty as `test_github_server_endpoints.py:262` does.
4. The unauthenticated half cannot be taken from the fixture's client: `httpx` merges per-request
   headers with the client's, so the fixture's `MCP_TEST_AUTH_HEADERS` cannot be removed. The 401 case
   uses the same app through a header-less `httpx.Client(transport=httpx.ASGITransport(app=...))`.
5. The mocked client's return values must be plain objects (not `MagicMock`) wherever a response model
   validates a field, because a `MagicMock` attribute fails pydantic validation; the mock is configured
   per case with `SimpleNamespace` values.

## Design decisions
- The service, validation, and dedup gate stay real; only the GitHub client is a `MagicMock`, so a
  refused call never reaches the API and a passing call is harmless — the same posture as
  `test_github_server_endpoints.py`'s `real_service` (line 244), which is not modified.
- The same-key concurrency test uses `httpx.AsyncClient` with `httpx.ASGITransport(app=...)` under
  `asyncio.gather`, because the shared fixture yields a synchronous `TestClient` and concurrency
  needs one event loop.

## Alternatives considered
- Threads over `TestClient`: rejected because the dispatcher's dedup path is asyncio-based and a
  thread-per-call run does not reproduce the single-loop acquisition the plan asserts.
- Asserting the in-process dispatch result object instead of the HTTP response: rejected because the
  row's contract is the HTTP boundary (status code plus `dedup_state` in the response body).

## Implementation
### Target file
`tests/mcp_servers/github/test_github_security_compliance.py` (new)

### Procedure
- Build the client from the shared fixture (`http_boundary`) and supply the upstream mock locally:
  a real `GitHubService` with `gh=MagicMock(...)` and a config whose `allowed_repos` names one
  repository, patched onto `github_server._service`.
- Add the enforcement cases listed in Method, each marked `@pytest.mark.security_contract`.

### Method
- Out-of-allowlist read (AC-1): `POST /v1/call_tool` for a repository outside `allowed_repos`
  returns 403 and the mocked client is never called (`_assert_allowed_repo`,
  `github_service_security.py:101`, reached through the boundary at line 311).
- Constrained global search (AC-1): with `allow_global_search=false` the query is scoped to one
  `repo:` qualifier per allowlisted entry (`github_service_security.py:267`), and a caller
  `repo:` or `org:`/`user:` qualifier outside the allowlist returns 403.
- Denied, oversized, and binary reads (AC-2): path-denylist match returns 403; a content metadata
  size above `max_file_read_size_kb` and non-UTF-8 content are reported as boundary error results
  (`is_error: true`, correction 1) — the size guard at `github_service_security.py:156` runs before
  the decode at `github_service_file.py:55` and 57-61, so the size error text is what the boundary
  returns for an oversized file.
- Unknown-argument rejection (AC-2): an extra key against a strict request model returns an error
  result at the boundary (correction 1), so the wire enforces the `additionalProperties: false`
  schema row 3 asserts is published.
- `dedup_state` (AC-4): a side-effecting write with `x-idempotency-key` reports the state from the
  injected store — `""` for the fresh acquisition (`dedup_gate.py:200`) and `duplicate_hit` or
  `in_progress` for a second call on the same key.
- Same-key concurrency (AC-4): two concurrent same-key writes through the ASGI async client execute
  the handler once (mocked client call count 1) and the other response carries
  `in_progress` or `duplicate_hit`, matching `tests/mcp_servers/test_mcp_dispatch_concurrency.py:113-121`.
- Authenticated and unauthenticated access (REQ-002): the same call returns 200 with
  `MCP_TEST_AUTH_HEADERS` and 401 without them.

### Details
- The dedup store is the one `isolated_dedup` injects; the test asserts the store path the fixture
  exposes rather than opening its own database.
- No test opens a path under `/opt/llm`; the suite's isolation guard applies unchanged.

## Compatibility considerations
- No existing test file is modified; the existing GitHub suite and
  `tests/mcp_servers/test_mcp_dispatch_concurrency.py` must keep passing.

## Security considerations
- The tests assert refusals at the boundary, so a guard that is bypassed fails the test rather than
  being masked by a stubbed response (Plan Design).

## Rollback considerations
- N/A: revert the commit — one new file.

## Validation plan
- `uv run ruff format tests/mcp_servers/github/test_github_security_compliance.py && uv run ruff check tests/mcp_servers/github/test_github_security_compliance.py`
- `uv run mypy --no-namespace-packages tests/mcp_servers/github/test_github_security_compliance.py`
- `uv run pytest tests/mcp_servers/github/test_github_security_compliance.py -v`
- `uv run pytest tests/mcp_servers/github/ -m security_contract -v` (marker selects this file)
- `uv run pytest tests/mcp_servers/github/ -q` and `uv run pytest tests/mcp_servers/test_mcp_dispatch_concurrency.py -v` (no regression)
- diff-cover ≥ 90% on changed lines per `rules/toolchain.md`

## Completion criteria
- Each enforcement case observes the documented refusal status at the HTTP boundary and the mocked
  client is not called for a refused call.
- `dedup_state` is present in the response body and a same-key concurrent write executes the handler
  exactly once.
- Authenticated access succeeds and unauthenticated access returns 401.

## Out of Scope
- Schema publication assertions (row 3).
- Fixing any behavior a test exposes (REQ-005).
- The CI/CD, Web Search, and MDQ test files that reuse the fixture.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-224731 | 20261126-224731 | — verified against source; no finding Step 3b corrections recorded: validation errors are boundary error results not 400; line citations for _resolve_search_query/_assert_max_read_file_size; _GITHUB_TOKEN patched; 401 half via header-less ASGI client |
| 2 | Add or update tests per Validation plan | N/A | — | — | this row is the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-224731 | 20261126-224731 | — ruff/mypy pass; end-of-batch full suite 15910 passed, diff-cover no measurable changed lines |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | no docs target in this Plan |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at procedure creation | N/A: no blocker recorded | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (HTTP-level security contract), `REQ-002` (authenticated and unauthenticated access)
- **Source issue**: issues/20261119-140517_mcpai010_github-http-contract-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-070112_mcpai010_github-http-contract-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-205430
- **Related target files**: `tests/mcp_servers/github/test_github_security_compliance.py`