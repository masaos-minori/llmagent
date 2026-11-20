# Secure Web Search MCP configuration, schemas, and audit behavior

## Priority
High

## Summary
Make Web Search MCP configuration and schemas strict and consistent, remove sensitive query and URL content from audit records, and audit every rejected call exactly once.

## Background
Source: consolidated Web Search and CI/CD MCP backlog (`memo-issue.md`, Issue 2).

Evidence (`Explicit in code`, by reading): `web_search_server.py` builds audit details with `query_preview={query[:80]!r}` and `url_preview={url[:80]!r}` and returns the raw query or URL as the audit target (lines 210-226); `scripts/mcp_servers/audit.py:28` shows `query_preview='search term'` in its docstring; the disabled-tool gate returns at line 269 before `extract_request_context` (line 271); `web_search_security_checks.py` reports malformed allowlist entries as a WARNING posture check (`_allowlist_check`, `_is_hostname_shape`). Schema drift claims are from the backlog and `Needs confirmation`.

## Problem
Raw queries and URLs (possibly with signed parameters, tokens, OAuth data, personal data) are retained in audit records. Disabled-tool calls are not audited. Malformed allowlist entries produce only warnings although they can never match runtime normalization. The `browser_fetch` schema may not reflect its model or the effective server limit.

## Reason for Change
Privacy and security-sensitive: sensitive content is persisted in logs, and rejected attempts are invisible to operators.

## Implementation Intent
Configuration errors fail at startup; discovery and runtime validation share one model; audit keeps correlation without retaining sensitive content; every authenticated call, including rejected ones, yields exactly one safe audit record. One normalization function serves configuration, posture, and runtime authorization.

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_models.py`, `web_search_tools.py`, `web_search_security_checks.py`, `web_search_server.py`
- `scripts/mcp_servers/audit.py`; `config/web_search_mcp_server.toml`
- `tests/mcp_servers/web_search/` schema, security-validation, server, audit, and health tests (`test_web_search_tool_schema.py`, `test_web_search_security_validation.py`, `test_web_search_audit.py`, `test_web_search_server.py`, `test_web_search_health.py`)
- `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md` and `docs/22_mcp/mcp_04_01_web-search-file-read-github.md` (see the document map of `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`)

## Required Changes
- Generate both tool schemas with the shared strict request base model and schema generator of `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md` (unknown fields rejected); the Web Search-specific constraints are a non-empty URL, the effective `max_response_kb` bounds, and aligning the model maximum with the server maximum or exposing clamping in the schema.
- Validate every allowlist entry at load time: normalize lowercase, IDNA ASCII, trailing dot; reject scheme, path, query, fragment, user information, port, non-string, blank, malformed, and duplicate entries; allow an empty list only as an intentional `browser_fetch` disabled configuration.
- Replace raw query targets with a normalized hash; remove query previews; strip URL query, fragment, and user information; keep scheme, normalized host, and a redacted path where needed; record only non-sensitive metadata (query length, host, result count, latency, status class, truncation flags).
- Move request-context extraction before disabled-tool rejection; audit disabled, unknown-tool, validation, authorization, and other rejections exactly once; rejected calls must not change provider health failure counts.
- Remove the plaintext query-preview example from shared audit documentation.
- Define the shared audit-emission contract in `scripts/mcp_servers/audit.py`: exactly one audit event for every authenticated call (success, rejection, and failure), a shared redaction helper (hashing of query-like values, URL stripping), and no raw values in audit records; the CI/CD and MDQ issues reuse them, and the audit-record fields (session, request, and logical call identifiers) follow `issues/20261119-140513_mcpai006_github-write-retry-policy.md`.

## Constraints
- An empty allowlist disables `browser_fetch` without weakening `search_web`.
- Existing audit consumers must tolerate the removed fields (`Needs confirmation`).

## Acceptance Criteria
- [ ] Public schemas and runtime models enforce the same contract for both tools, with drift coverage.
- [ ] Malformed allowlist entries fail startup; valid normalized entries match runtime host normalization.
- [ ] Raw queries and sensitive URL components never appear in standard audit JSON; signed URLs and token-shaped values are redacted.
- [ ] Disabled and rejected authenticated calls emit exactly one audit record.
- [ ] An empty allowlist cleanly disables `browser_fetch`.

## Testing Expectations
- Extend schema parity to `browser_fetch`; reverse warning-based malformed-allowlist expectations to startup failures; add uppercase, IDNA, trailing-dot, scheme, path, port, blank, non-string, and duplicate cases.
- Replace plaintext audit expectations with redaction expectations; add signed URL, token, OAuth parameter, personal-data, and disabled-tool audit tests; verify exactly one record per outcome category.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Allowlist normalization and matching rules; search-result URLs are not automatically authorized for `browser_fetch`; health wording that does not imply constant health; separate current health from historical error metadata; Bearer authentication in `/v1/tools` examples.

## Out of Scope
- Network authorization and resource limits (`issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md`).
- CI/CD audit (`issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md`).

## Dependencies
- No blocking dependency; can run in parallel with `issues/20261119-141107_mcpws001_websearch-fetch-network-boundary.md`. Archived `issues/done/20261026-220730_mcp006-web-search-broad-except-in-call-tool.md` touched the same call path; re-verify against current source.
- Depends on `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md` (shared schema generator) and `issues/20261119-140509_mcpai002_github-read-security-boundary.md` (shared strict configuration helpers). Blocks `issues/20261119-141111_mcpci004_cicd-error-audit-coverage.md` and `issues/20261119-142123_mdqmcp001_mdq-server-boundary.md`, which reuse the shared audit-emission contract and redaction helper.

## Unresolved Questions
- `不明`: path redaction rule for URL audit targets.
- `不明`: existing readers of `query_preview` or `url_preview` in audit tooling.

## AI Implementation Instruction
Keep audit field removal and the exactly-once change in separate tested steps. Do not log new sensitive data while debugging. Stop and report if an audit consumer depends on the removed fields.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-141108
- **Related target files**: `scripts/mcp_servers/web_search/web_search_models.py`, `scripts/mcp_servers/web_search/web_search_tools.py`, `scripts/mcp_servers/web_search/web_search_security_checks.py`, `scripts/mcp_servers/web_search/web_search_server.py`, `scripts/mcp_servers/audit.py`, `config/web_search_mcp_server.toml`
