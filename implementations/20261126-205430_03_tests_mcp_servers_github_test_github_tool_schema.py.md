## Goal

Create the `/v1/tools` schema-publication contract tests (REQ-001, AC-3): the schemas a client
discovers over HTTP are the generated strict model schemas, including `dry_run`, asserted through
the shared HTTP fixture (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The root conftest sets `MCP_GITHUB_AUTH_TOKEN` (`tests/conftest.py:338-345`), so importing
  `scripts/mcp_servers/github/github_server.py` succeeds in the test environment; the GitHub API
  token is not set, which is why the schema assertions use `?include_disabled=true` (the pattern
  at `tests/mcp_servers/github/test_github_server_endpoints.py:268-273`).
- `build_input_schema` (`scripts/mcp_servers/request_contract.py:44`) emits
  `additionalProperties: False` for the strict base (`StrictRequestModel`, same file line 34), so
  strictness is observable on the wire, not only in-process.
- The fixture named in this document is the one row 1 creates; it is not created here.

## Design decisions
- Assert the wire payload against `build_input_schema(model)` for the file tools, so the test
  proves the published schema is the model schema rather than a hand-written expectation.
- Every test in this file carries `security_contract` (new) as its pytest marker (REQ-004); no characterization
  test is added here.

## Alternatives considered
- Extending `tests/mcp_servers/github/test_github_tool_registry.py`'s in-process equality gate:
  rejected because that gate does not observe the HTTP payload, and the Plan's row is a new file
  asserting the wire shape.
- Asserting a fixed expected schema dict: rejected because it duplicates the model and can drift
  while the wire contract still passes.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_tool_schema.py` (new)

### Procedure
- Import the shared fixture's client through the fixture parameter `http_boundary`, the GitHub
  server module, and the request models whose schemas are asserted.
- Add one test class with the schema-publication cases listed in Method.

### Method
- `test_file_tool_schemas_are_the_generated_model_schemas` (new): `GET /v1/tools?include_disabled=true`,
  then for each file tool compare `inputSchema` with `build_input_schema(<RequestModel>)`.
- `test_published_schemas_are_strict` (new): every published `inputSchema` has
  `additionalProperties` false, so the wire advertises the same posture `_validate_request`
  enforces (`scripts/mcp_servers/github/github_service_dispatch_writes.py:68`).
- `test_write_tools_publish_dry_run` (new): each `is_write` tool publishes `dry_run` as a boolean
  with default `false` (AC-3).

### Details
- The file tools asserted are the ones in `scripts/mcp_servers/github/tools_file.py`'s `TOOL_LIST`
  (the row's evidence at line 69); the write-tool set is taken from the response's `is_write` flag
  rather than a hard-coded count, so the test does not duplicate
  `test_github_server_endpoints.py`'s pinned count of 9.
- Tests are synchronous (`TestClient`), marked `security_contract` (new), and read no production path.

## Compatibility considerations
- No existing test file is touched; the new file only consumes the fixture from row 1.

## Security considerations
- The client authenticates with `MCP_TEST_AUTH_HEADERS`, so the assertions run on the authenticated
  boundary the contract is defined at (REQ-002 coverage lives in row 4).

## Rollback considerations
- N/A: revert the commit — one new file.

## Validation plan
- `uv run ruff format tests/mcp_servers/github/test_github_tool_schema.py && uv run ruff check tests/mcp_servers/github/test_github_tool_schema.py`
- `uv run mypy --no-namespace-packages tests/mcp_servers/github/test_github_tool_schema.py`
- `uv run pytest tests/mcp_servers/github/test_github_tool_schema.py -v`
- `uv run pytest tests/mcp_servers/github/ -m security_contract -v` (marker selects this file)
- `uv run pytest tests/mcp_servers/github/ -q` (existing characterization tests keep passing)
- diff-cover ≥ 90% on changed lines per `rules/toolchain.md`

## Completion criteria
- The published `inputSchema` for each file tool equals the generated model schema, strictness is
  visible on the wire, and every write tool publishes `dry_run` with a false default.
- All tests in the file are selected by `-m security_contract` and the existing GitHub suite is
  unchanged.

## Out of Scope
- Runtime enforcement at `/v1/call_tool` (row 4).
- Fixing any behavior a test exposes: report it against the owning issue (REQ-005).

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | — |
| 2 | Add or update tests per Validation plan | N/A | — | — | this row is the test file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | — |
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
- **Requirement ID**: `REQ-001` (HTTP-level security contract, schema publication), `REQ-003` (shared HTTP fixture consumer)
- **Source issue**: issues/20261119-140517_mcpai010_github-http-contract-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-070112_mcpai010_github-http-contract-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-205430
- **Related target files**: `tests/mcp_servers/github/test_github_tool_schema.py`
