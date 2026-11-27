## Goal

Add the reusable HTTP-level MCP test fixture (REQ-003, shared HTTP fixture) that the
GitHub contract tests and the sibling MCP issues consume, so a security-contract test can
drive the real FastAPI boundary with only the upstream API client mocked.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The fixture is additive: no existing fixture, autouse fixture, or test file is changed.
- `tools/check_conftest_integrity.py` inspects the root `tests/conftest.py` only, so for this
  row it confirms the required autouse fixtures are intact but does not check the new fixture;
  the new fixture is validated by the tests that consume it (Plan Tests section, corrected in
  Step 3a).
- The fixture does not mock any upstream client: each consuming file supplies its own mock, per
  the Plan's Design decisions.

## Design decisions
- The fixture composes the existing `isolated_dedup` fixture (`tests/mcp_servers/conftest.py:111`)
  rather than adding a second dedup mechanism, so the dedup gate stays the injection-only contract
  (mcpdl003 REQ-001) and the same-key concurrency test observes the real store.
- One factory fixture, not a per-server fixture: it takes the server module and returns a
  `TestClient` bound to that module's `app` with `MCP_TEST_AUTH_HEADERS`, so the same fixture
  serves every MCP server directory.

## Alternatives considered
- A GitHub-specific fixture in `tests/mcp_servers/github/`: rejected because REQ-003 requires a
  fixture reusable by the sibling MCP issues, and a directory-local conftest is not visible to
  sibling directories.
- An autouse fixture: rejected because the suite's autouse fixtures are the isolation guards
  tracked by `tools/check_conftest_integrity.py`; a test-scoped fixture keeps opt-in behavior.

## Implementation
### Target file
`tests/mcp_servers/conftest.py`

### Procedure
- Add the imports the fixture needs: `from fastapi.testclient import TestClient` and
  `from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS`.
- Add one non-autouse fixture, `http_boundary` (new), that depends on `isolated_dedup` and yields
  a factory callable.
- Add the schema-assertion helper `tool_schema` (new) as a method of the object the factory returns,
  so a contract test can read the published `inputSchema` for one tool name.

Step 3b correction (20261126): `monkeypatch` is dropped as a fixture dependency — the fixture
creates no patch; `isolated_dedup` already owns the injection and its cleanup, and each consuming
file supplies its own mock. The factory cannot return a bare `TestClient` with an added method and
attribute (a third-party class, not type-safe to extend), so it returns the new `HttpBoundary`
helper object holding `client`, `dedup_path`, and `tool_schema()`.

### Method
- `http_boundary` (new) yields a factory that takes a server module (for example
  `mcp_servers.github.github_server`) and returns an `HttpBoundary` (new) wrapping
  `TestClient(module.app, headers=MCP_TEST_AUTH_HEADERS)`. The helper exposes the composed dedup
  path as an attribute so a test can assert the store the fixture injected, matching the pattern
  already used at `tests/mcp_servers/github/test_github_server_endpoints.py:505`.
- `tool_schema` (new) calls `GET /v1/tools` through the same client and returns the `inputSchema`
  dict for a tool name, so schema publication and runtime enforcement are asserted from the same
  boundary.
- The factory keeps the service, validation, and dedup gate real; only the caller's own upstream
  mock is supplied by the consuming test file.

### Details
- Existing fixtures in this file (`_emulate_dedup_bootstrap`, `_propagate_server_loggers`,
  `isolated_dedup`) stay unchanged and in the same order; the new fixture is appended after
  `isolated_dedup`.
- The factory must not call any config discovery: `isolated_dedup` already injects the store
  through the dispatch module's configure seam.

## Compatibility considerations
- Existing MCP server tests keep their own local fixtures; nothing imports the new fixture yet,
  so no current test changes behavior.
- `skills/mcp-server-add/workflow.md:162` names this file as the place for shared MCP fixtures, so
  the fixture is consistent with the documented pattern.

## Security considerations
- The fixture authenticates with the shared test token headers, so an unauthenticated request is
  still observable as a 401 rather than being masked by the fixture.

## Rollback considerations
- N/A: revert the commit — the change is one additive fixture block in one file.

## Validation plan
- `uv run ruff format tests/mcp_servers/conftest.py && uv run ruff check tests/mcp_servers/conftest.py`
- `uv run mypy --no-namespace-packages tests/mcp_servers/conftest.py`
- `uv run python tools/check_conftest_integrity.py` (required autouse fixtures intact)
- `uv run pytest tests/mcp_servers/github/test_github_tool_schema.py tests/mcp_servers/github/test_github_security_compliance.py -v`
  (the consuming files prove the fixture works)
- `uv run pytest tests/mcp_servers/github/ tests/mcp_servers/test_mcp_dispatch_concurrency.py -q` (no regression)

## Completion criteria
- The fixture is importable by both new GitHub test files and yields a working `TestClient` for the
  real GitHub app.
- The dedup store the fixture composes is the same `isolated_dedup` tmp DB, so a same-key call
  reports a dedup state from the real store.
- No existing fixture or autouse fixture in the file changed, and the conftest-integrity gate passes.

## Out of Scope
- No modification of `tests/mcp_servers/github/test_github_server_endpoints.py` or any other
  existing test file.
- No documentation change: the Plan records `Documentation Impact` as N/A.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-000000 | 20261126-000000 | — tests/mcp_servers/conftest.py; Step 3b correction: factory returns the HttpBoundary helper object, monkeypatch dependency dropped |
| 2 | Add or update tests per Validation plan | Completed | — | 20261126-222434 | — targeted tests pass (testmon selection, 6716 passed); the fixture itself is proven by rows 3 and 4 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-222434 | 20261126-224731 | — ruff/mypy/conftest-integrity pass; awaiting the end-of-batch full-suite run end-of-batch full suite 15910 passed; diff-cover reports no measurable changed lines (coverage source is scripts/) |
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
- **Requirement ID**: `REQ-003` (reusable HTTP-level MCP fixture)
- **Source issue**: issues/20261119-140517_mcpai010_github-http-contract-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-070112_mcpai010_github-http-contract-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-205430
- **Related target files**: `tests/mcp_servers/conftest.py`