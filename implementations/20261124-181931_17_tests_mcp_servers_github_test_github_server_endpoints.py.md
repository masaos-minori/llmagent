## Goal
Prove at the HTTP boundary that the published schema and the runtime now agree: `/v1/tools` serves the
generated schemas, and `/v1/call_tool` rejects exactly the inputs those schemas advertise — with an
error result and no GitHub service call — instead of silently dropping unknown keys (T-05, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

- Modifies only `tests/mcp_servers/github/test_github_server_endpoints.py` (Plan Phase 6).
- Existing classes (`TestToolsListEndpoint`, `TestCallToolEndpoint`, `TestHealthEndpoint`,
  `TestDispatchGithubTool`, `TestGithubMCPServerDispatch`, `TestCallToolBoundary`) keep their behavior;
  only assertions that encode the old key-picking behavior are updated.

## Assumptions
- The strict dispatch (`_validate_request`, seq 12-13) is what the endpoint reaches through
  `github_server.py:198` (`_service.get_dispatch_table()` -> `dispatch_tool`).
- Verified today: `CallToolResponse` (`scripts/mcp_servers/models.py:56-64`) publishes only `result`,
  `is_error`, `dedup_state`; `error_type="validation_error"` (`scripts/mcp_servers/dispatch.py:470`)
  is visible in the audit record (`scripts/mcp_servers/audit.py` `mcp_tool_exec` entry), not in the
  HTTP body. HTTP status stays 200 for a validation failure; there is no 422 contract in this
  repository (Plan REQ-008 correction, Step 3a).
- The file's existing `_FakeService` replaces the whole dispatch table with `AsyncMock` handlers, so it
  bypasses model validation; the new class needs the **real** dispatch table with the GitHub client and
  the domain service methods mocked below the validation point.

## Design decisions
- New `class TestCallToolValidation` builds a real `GitHubService(gh=MagicMock(),
  cfg=GitHubConfig.from_dict({...}))` (the pattern already used by `test_service_dispatch.py:70`),
  monkeypatches `github_server._service` with it, and patches the domain entry points
  (`svc.search_repositories`, `svc.create_issue`, `svc.push_files`, ...) with `AsyncMock` so a call
  that reaches the service layer is both detectable and harmless.
- Rejection cases are one parametrized table of `(tool_name, args)` pairs covering one case per newly
  rejected input class from seq 12-13 (unknown key, missing required key, empty identifier,
  `per_page` 0/101, oversized `content`, empty `files`, nested unknown key, no-op PR update); each
  asserts `status_code == 200`, `is_error is True`, and every domain `AsyncMock` `assert_not_awaited()`.
- Acceptance counterpart: the same tools with minimal valid args reach the mocked domain method
  (`assert_awaited_once`), proving the new strictness did not break the happy path.
- A `/v1/tools` test asserts the generated contract is visible on the wire: for every write tool,
  `dry_run` appears in `inputSchema.properties`; for `github_search_repositories`, `properties.per_page`
  carries `minimum: 1`, `maximum: 100`, `default: 30`; for `github_push_files`,
  `inputSchema` contains `$defs` with a `PushFile` entry. This checks the endpoint payload, complementing
  seq 14's in-process equality gate.

## Alternatives considered
- Testing validation through `_FakeService` with real `fmt_*` handlers attached: rejected — a hand-built
  dispatch table drifts from the real one; the real service object is the subject under test.
- Asserting `error_type` from the HTTP body: rejected — the response model does not carry it; the audit
  assertion (`logger`-level inspection, already used at lines 176-177) is the existing way to observe it.

## Implementation
### Target file
`tests/mcp_servers/github/test_github_server_endpoints.py`

### Procedure
1. Add the real-service fixture (new) next to `fake_service`, patching `github_server._service` and the
   domain methods named in Design decisions.
2. Add `TestCallToolValidation` (new) with the parametrized reject table, the happy-path accept cases, and one
   audit-record test asserting the failure is recorded with `error_type="validation_error"`.
3. Extend `TestToolsListEndpoint` with the schema-shape assertions from Design decisions (generated
   schema visible on `/v1/tools`).
4. Update only existing assertions that contradict the new behavior (for example any fixture args that
   rely on unknown keys being dropped); keep every unrelated assertion intact.

### Method
- Reject table reuses the same boundary values as seq 15 (101 `per_page`, 1048577-char `content`) so the
  model-level and HTTP-level suites assert the same numbers.

### Details
- The no-op `github_update_pull_request` case reaches validation only after seq 04's model validator and
  seq 13's conversion land; it is added in the same commit as seq 13.
- Keep the disabled-token gate untouched: fixtures continue to set `_GITHUB_TOKEN` to a fake value so
  validation, not the gate, produces the error.

## Compatibility considerations
- Existing tests in this file that pin 200/403/503 outcomes are unaffected; only assertions built on the
  silent-drop behavior change.
- The file's `TestDispatchGithubTool`/`TestGithubMCPServerDispatch` call dispatch directly and must keep
  passing with the new dispatch builders (they exercise the same `fmt_*` methods).

## Security considerations
- "No service method awaited" is the HTTP-level proof of AC-03/AC-04: rejected payloads never reach the
  allowlist check or the GitHub API.

## Rollback considerations
- Revert with the Phase 6 commit; the new class is additive except for the explicitly listed assertion
  updates.

## Validation plan
- `uv run pytest tests/mcp_servers/github/test_github_server_endpoints.py` (T-05).
- `uv run pytest tests/mcp_servers/github/` after seq 12-13 land (T-06).
- `uv run ruff check tests/mcp_servers/github/test_github_server_endpoints.py`, `uv run mypy`,
  `uv run diff-cover coverage.xml --compare-branch=master` (>= 90% on changed lines).

## Completion criteria
- Every rejected-input class listed in seq 12-13 has a failing-call test asserting 200 + `is_error`
  with no domain method awaited.
- `/v1/tools` exposes `dry_run` on all write tools, the pagination bounds, and the `github_push_files`
  `$defs`/`$ref` shape.
- The whole GitHub test directory passes.

## Out of Scope
- Model-level boundary matrices (seq 15), the drift gate (seq 14), `exception_handlers.py` behavior
  (`test_github_exception_handlers.py`, unchanged), docs (seq 18-19).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the real-service fixture and `TestCallToolValidation` (new) | Pending | — | — | T-05; needs seq 12-13 |
| 2 | Add `/v1/tools` generated-schema assertions | Pending | — | — | REQ-002, REQ-003 |
| 3 | Update existing assertions that encoded silent-drop behavior | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) for this file | Pending | — | — | T-06 |

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
- **Requirement ID**: `REQ-008` (runtime validation aligned with the published schema at the HTTP boundary), `REQ-002`/`REQ-003` (schemas and `dry_run` visible on `/v1/tools`)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `tests/mcp_servers/github/test_github_server_endpoints.py`
