# Correct CI/CD error classification and guarantee complete audit coverage

## Priority
Medium

## Summary
Map GitHub API and transport failures accurately and emit exactly one safe audit event for every authenticated CI/CD tool call, including rejected and failed calls.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 8).

Evidence (`Explicit in code`, by `rg`): `cicd_service_github_actions.py` raises `CicdNotFoundError` (lines 71, 78), and `exception_handlers.py:39` maps it to HTTP 404; the 5xx-to-404 mapping claim is from the backlog and `Needs confirmation` for the exact branch. `cicd_server.py` calls `_audit_log` (line 177) inside the dispatch function; whether it runs for disabled and rejected paths is `Needs confirmation`.

## Problem
GitHub 5xx can surface as Not Found, hiding outages and misleading recovery; audit occurs after successful dispatch, so disabled, validation, authorization, upstream, and unexpected failures may produce no event.

## Reason for Change
Truthful errors and complete audit are needed for recovery decisions and incident review; final names depend on the dedup and credential contracts.

## Implementation Intent
Truthful, machine-readable errors and one correlated, redacted audit event per authenticated call, produced by a `try/except/finally` structure.

## Target Files or Areas
- CI/CD GitHub Actions backend error mapping; `scripts/mcp_servers/cicd/exception_handlers.py`, `cicd_server.py`
- `scripts/mcp_servers/audit.py`
- `tests/mcp_servers/cicd/test_cicd_exception_handlers.py`, `test_cicd_server_endpoints.py`, `test_service_github_actions_error_edges.py`; a new `tests/mcp_servers/cicd/test_cicd_audit.py` (absent today)

## Required Changes
- Map 5xx to `CicdUpstreamError`; add a distinct rate-limit error for 429; map DNS, TLS, connection, and timeout failures to upstream errors; map 409 to a conflict error; preserve safe `Retry-After` and reset metadata; bound and redact upstream error text.
- Restructure `call_tool()` around `try/except/finally`; audit success, disabled, unknown tool, validation, authorization, upstream, dedup, and unexpected outcomes with `ok`, `error`, `rejected`; record session id, request id, logical call id, tool, normalized target, latency, and stable error code; never record tokens or workflow input values.
- Remove the duplicate `requested_target` assignment in the shared audit helper; make audit failure follow the documented server policy.

## Constraints
- Exactly one event per authenticated call; no credentials, workflow inputs, or raw upstream payloads in audit or errors.

## Acceptance Criteria
- [ ] GitHub 500 and 503 become upstream errors, not 404; 429 is distinct.
- [ ] 401, 403, 404, 409, and 422 retain appropriate semantics.
- [ ] Every authenticated call emits exactly one audit event, including disabled and allowlist-rejected calls and exceptions.
- [ ] Credentials, workflow input values, and raw upstream payloads are absent.

## Testing Expectations
- Reverse the existing HTTP 500 to Not Found expectation; add 401, 403, 404, 409, 422, 429, 500, 503, DNS, TLS, and timeout cases; cover every result category and audit serialization failure.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. An error mapping table; separate Agent audit log and MCP server application and audit event terminology; exactly-one-event behavior and redaction rules.

## Out of Scope
- Dispatch reconciliation states (`issues/20261119-141109_mcpci002_cicd-dispatch-reconciliation.md`); web search audit (`issues/20261119-141108_mcpws002_websearch-config-audit-redaction.md`).

## Dependencies
- Depends on `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md`, `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` (final state names), and `issues/20261119-141106_mcpci001_cicd-credential-config-contract.md` (credential metadata). Scaffolding may start earlier; finalization follows them.

## Unresolved Questions
- `不明`: the documented audit-failure policy for the CI/CD server.
- `不明`: the exact code path that maps 5xx to Not Found.

## AI Implementation Instruction
Write the 500-not-404 and exactly-one-event tests first. Keep changes inside the CI/CD server, shared audit helper, and tests. Stop and report if the shared audit helper change affects other servers.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141111
- **Related target files**: `scripts/mcp_servers/cicd/exception_handlers.py`, `scripts/mcp_servers/cicd/cicd_server.py`, `scripts/mcp_servers/audit.py`, `tests/mcp_servers/cicd/`
