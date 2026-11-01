# Tool-level "not found" and "forbidden" results trip the MCP server health circuit

## Priority
High

## Summary
The file MCP servers report ordinary tool outcomes ("file does not exist", "path outside allowed directories") as HTTP 404 and 403 through FastAPI exception handlers. `HttpTransport.call` turns every non-retryable non-2xx response into a `TransportError`, and the invoker counts each one as a health failure. Three such results in a row mark the whole server UNAVAILABLE for the cooldown period, after which every tool of that server is rejected without any HTTP request. A model that guesses file paths can cause this in one round. Make tool-level outcomes carried by HTTP status codes stop counting as server health failures.

## Background
Found during an adversarial review (`python-code-review`) of the agent's MCP call path.
- Server side: `mcp_servers/file/common.py` builds the handlers `_on_auth_error` (403), `_on_not_found` (404) and `_on_validation_error` (422). `read_server.py`, `write_server.py` and `delete_server.py` register them for `FileAuthorizationError`, `FileNotFoundError` and `FileValidationError`. `dispatch_tool` converts only `ValueError` into a 200 response with `is_error=true`; `FileNotFoundError` (an `OSError`) and `FileAuthorizationError` (a `RuntimeError`) are not caught there, so they reach the HTTP handlers. (`FileValidationError` is a `ValueError`, so dispatch answers it first with 200; its 422 handler is probably unreachable for tool calls.)
- Client side: `HttpTransport.call` handles `httpx.HTTPStatusError` for statuses outside the retryable set by raising `TransportError` immediately. `ToolTransportInvoker._invoke_and_record` passes it to `_record_transport_error`, which calls `McpServerHealthRegistry.record_failure` (threshold 3, half-open cooldown 30 seconds by default). While UNAVAILABLE, `_check_health` rejects the call before any HTTP request and returns an availability hint.
- `docs/22_mcp/mcp_03_03_transport-and-health.md` states that non-2xx HTTP raises `TransportError` (`Documentation only` for the policy; the code matches it). The related archived issue `issues/done/20261005-121408_trn001_http-tool-level-errors-are-reported-with-error_type-transport-instead-of-tool.md` fixed the classification of HTTP 200 responses that carry `is_error=true`; this issue is the same principle for tool outcomes that the server signals with a 4xx status, which that fix did not cover.

## Problem
Reproduction (throwaway script, not committed): a `ToolTransportInvoker` with a real `HttpTransport` and `McpServerHealthRegistry`, and an `httpx.MockTransport` that answers a read of a missing path with HTTP 404 and anything else with a normal 200 result. Observed: three calls for the missing path each return `error_type="transport"`, with health states degraded, degraded, unavailable. A fourth call for an existing path then returns "MCP server 'file_read' is currently unavailable (health check failed)" with `error_type="tool"`, zero HTTP requests are sent, and the hint reports `retry_after_seconds=30`. The mock reproduces the status code only; the real servers were not started, and the 404/403 mapping is established by reading the server code.

Consequences:
- Normal model behavior (probing paths that do not exist, or paths outside the allowed directories) blocks all read tools for the cooldown period, including reads of valid files.
- Each such result is also written as a transport failure diagnostic (`_record_transport_failure` fires for `error_type="transport"`), and counts toward the per-server unavailable-repeat guard, so a turn can be stopped for a reason that is not a server failure (`Needs confirmation`: the guard threshold is `tool_empty_result_max_repeats`).
- Parallel reads in one round (a concurrent group of read calls) can reach three failures within a single round.

## Reason for Change
The health circuit exists to detect a sick server. Here it is driven by the model's own mistakes against a healthy server, and the failure mode is a self-inflicted outage of the read tools for 30 seconds at a time. This is a normal-use runtime failure, not an edge case.

## Implementation Intent
Separate "the server is unhealthy" from "the server answered that this request is not possible". Either make the file servers report these outcomes in the same way as other tool errors (HTTP 200 with `is_error=true`, as the dispatch layer already does for `ValueError`), or make the client recognize a defined set of tool-level statuses and return a tool-level error result that records a successful transport call. Keep authentication failures (401), timeouts, malformed responses, retry exhaustion and 5xx as transport failures. The owner chooses which side changes; the two sides must agree on one documented contract.

## Target Files or Areas
- `scripts/shared/http_transport.py` (`HttpTransport.call`, handling of `httpx.HTTPStatusError`)
- `scripts/shared/tool_transport_invoker.py` (`_invoke_and_record`, `_record_transport_error`)
- `scripts/mcp_servers/file/common.py` (the 403/404/422 handlers)
- `scripts/mcp_servers/file/read_server.py`, `write_server.py`, `delete_server.py` (handler registration)
- `scripts/mcp_servers/dispatch.py` (`dispatch_tool`, which exception types become tool errors)
- the other servers' error handlers (github, git, web_search, rag_pipeline; cicd, mdq and shell still to be checked)
- `docs/22_mcp/mcp_03_03_transport-and-health.md`
- `tests/shared/`, `tests/mcp_servers/`, `tests/integration/` tests for transport classification and health

## Required Changes
- Define which HTTP statuses on `/v1/call_tool` are tool-level outcomes and which are transport failures, and implement that on one side consistently.
- Ensure a tool-level outcome results in `error_type="tool"` (or an equivalent non-transport result), calls the success path of the health registry, and does not write a transport failure diagnostic.
- Check the other MCP servers (git, github, cicd, rag, mdq, web search, shell) for statuses used the same way and apply the same contract.
- Add tests: three consecutive not-found results leave the server HEALTHY and a following valid call is sent; a 401, a timeout and a 500 still count as failures.

## Constraints
- Do not change the failure threshold or cooldown of `McpServerHealthRegistry`.
- Keep the fail-closed retry rules for write tools (no retry after an ambiguous post-send failure).
- Keep 401 as a transport/health failure so a wrong token is still visible.
- Do not change the `TransportError` type or its message format for real transport failures.
- Tests must not start real servers or touch production state.

## Acceptance Criteria
- Three consecutive file-not-found or outside-allowed-directory results do not change the server's health state and do not block the next valid call.
- Such results are reported to the model as tool errors, with a message that carries the server's reason.
- A 401, a timeout, a malformed response and a 5xx still produce transport failures and health failures.
- The documentation states the HTTP-status contract between the servers and the client.
- The new tests fail on the current code and pass after the change.

## Testing Expectations
- Unit tests for `HttpTransport.call` and `ToolTransportInvoker` with `httpx.MockTransport` and a real `McpServerHealthRegistry`.
- A server-side test that a missing file and an outside-directory path produce the agreed response, using the app's test client with a temporary allowed directory.
- Regression: run `tests/shared`, `tests/mcp_servers` and the MCP integration tests; run `ruff` and `mypy --no-namespace-packages` on touched files.

## Documentation Impact
Update `docs/22_mcp/mcp_03_03_transport-and-health.md` (and any page that repeats the "non-2xx is a transport failure" rule) to state which statuses are tool-level outcomes and which are transport failures, and why. Describe intent and boundaries only; do not copy concrete thresholds.

## Out of Scope
- Health thresholds, cooldown length, or the half-open trial design.
- The classification of HTTP 200 responses with `is_error=true` (done in the archived `trn001` issue).
- Retry and idempotency behavior.

## Dependencies
N/A: none. `issues/done/20261005-121408_trn001_http-tool-level-errors-are-reported-with-error_type-transport-instead-of-tool.md` is archived background only. No open issue or plan targets `http_transport.py` or `mcp_health.py` for this behavior.

## Unresolved Questions
- Whether the server or the client should change: `Needs confirmation`; the contract must be decided once and documented.
- Which other MCP servers return non-2xx for tool outcomes: the github server returns 400, 403, 404, 409, 500 and 502, the git server returns 500 for its service errors, web_search returns 403, 422 and 502, and rag_pipeline returns 503 (`Explicit in code`; read in a follow-up verification). The cicd, mdq and shell servers were not checked (`Needs confirmation`). The contract decision must cover these servers too.
- Whether the per-server unavailable-repeat guard actually stops a turn in this case: `Needs confirmation`.

## AI Implementation Instruction
Decide the HTTP-status contract first and record it in the issue or plan before editing. Change only the classification of tool-level statuses and the matching tests and documentation. Keep 401, timeouts and 5xx as failures. Stop and report if the fix needs a change to the health registry itself.

## Traceability
- **Workflow phase**: python-code-review -> issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261101-073450
- **Related target files**: scripts/shared/http_transport.py, scripts/shared/tool_transport_invoker.py, scripts/mcp_servers/file/common.py, scripts/mcp_servers/file/read_server.py, scripts/mcp_servers/file/write_server.py, scripts/mcp_servers/file/delete_server.py, scripts/mcp_servers/dispatch.py, docs/22_mcp/mcp_03_03_transport-and-health.md
