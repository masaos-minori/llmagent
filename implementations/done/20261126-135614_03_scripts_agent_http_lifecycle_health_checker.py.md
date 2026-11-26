## Goal
- Apply the per-server health timeout and the remaining-deadline cap in the startup poll, route health auth through `auth_headers()` only, and replace the `liveness`-only predicate with report-based readiness in `http_lifecycle_health_checker.py` (REQ-001, REQ-002, REQ-003, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `poll_until_ready`, `verify_running_async`, and the readiness predicate in this file.
- Out of scope: the caller passing the per-server timeout (seq 04); the contract module (seq 01); the test updates (seq 20).

## Assumptions
- Verified in Step 3a: `compute_health_check_timeout()` caps by `min(mcpserver_health_timeout, startup_timeout)` (`:92-101`), not by the remaining deadline; `verify_running_async` defaults to 5.0 (`:249`) and rebuilds the Bearer header from `cfg.auth_token` (`:267-271`), a second header path; `is_degraded_but_live` (`:104`) accepts a 503 with `liveness=true` (`:199`).
- Readiness here means: the parsed report proves the server's `required_capability` is `ok`, or the body is legacy and `ready` is true (D-6).
- Corrected in Step 3b: `required_capability` is passed to `poll_until_ready` as a keyword argument by the caller (seq 04); the checker does not read `config/tool_catalog.toml` (owner decision, 2026-11-26). The readiness helper takes `(report, required_capability)`.
- Corrected in Step 3b: readiness is decided from the parsed report alone, not from the status code; a body that is not JSON, is not an object, or violates the contract is not proof and the poll keeps running.
- Corrected in Step 3b: the deadline cap is applied per request through `client.get(..., timeout=...)`; the client keeps the effective timeout as its default. `required_capability` defaults to `None` (read through the legacy `ready` fallback) so existing call sites keep working until seq 04 resolves it.
- Corrected in Step 3b: `compute_health_check_timeout()` is removed. It was the implementation of the rejected alternative (`min(effective, startup_timeout)`) and has no remaining consumer (`rg` over `scripts/`, `tests/`, `docs/` finds only its definition), so keeping it would leave a dead helper with a hard-coded 5.0 default that contradicts REQ-001.
- UNK-02 (Plan Risk mitigation): before deploy, check the production health samples under `/opt/llm` for a required server that returns a 503 with `ready=false` and no capability block; the report-based readiness rule here is what would block its startup, so start every server in staging first.

## Design decisions
- D-4: startup request timeout is `min(effective, remaining time to the deadline)`; no request starts after the deadline.
- D-1: the second header-building path is removed; `cfg.auth_headers()` is the only source.

## Alternatives considered
- Leave `min(effective, startup_timeout_sec)` (rejected by D-4: a request can outlive the deadline).

## Implementation
### Target file
`scripts/agent/http_lifecycle_health_checker.py`

### Procedure
1. In `poll_until_ready`, compute each request timeout as `min(effective health timeout, remaining time to the deadline)` and skip the request once the deadline has passed.
2. Replace `is_degraded_but_live` with a report-based readiness check that parses the body through `shared.mcp_health_contract` and requires the required capability to be proven `ok` (legacy bodies fall back to `ready`).
3. In `verify_running_async`, use the per-server effective timeout instead of the 5.0 default and send headers only through `cfg.auth_headers()`.

### Method
- Readiness helpers (new): `parse_report(resp)` returns the parsed `HealthReport` or `None` for an unparseable body; `is_ready(report, required_capability)` returns true only when that capability is `ok` or the body is legacy with `ready=true`. Both are reused by seq 05.
- Keep the shutdown-aware poll sleep unchanged; the deadline cap only bounds the per-request timeout.

### Details
- The health failure log line must not contain the token (REQ-003); the existing log format already logs the URL and status only — confirm no token is interpolated.

## Compatibility considerations
- `is_degraded_but_live` is referenced by tests pinned at `test_http_lifecycle_health_check.py:392-467` (seq 20 updates them); callers pass the timeout explicitly (seq 04).

## Security considerations
- One auth path only; the token never appears in a health log line or error message.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_integration.py`; `uv run ruff format` and `uv run ruff check`; `uv run mypy`; then the sequence in `rules/toolchain.md`.

## Completion criteria
- A request issued with `T` seconds left has timeout `min(effective, T)`; no request starts after the deadline; a liveness-only 503 no longer passes; every health request uses `auth_headers()`; tests pass.

## Out of Scope
- The caller-side timeout plumbing and the test file itself.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the timeout cap, single auth path, and report-based readiness | Completed | 20261126-170920 | 20261126-170920 | Changed: parse_report/is_ready static helpers, required_capability keyword arg on poll_until_ready, per-request timeout min(effective, remaining), no request after the deadline, verify_running_async resolves get_effective_health_timeout(cfg) and uses cfg.auth_headers() only. Removed is_degraded_but_live, _DEFAULT_TIMEOUT, compute_health_check_timeout (no remaining consumers). File size 20449 B < 24576. |
| 2 | Tests are covered by the test-file procedure (seq 20) | Completed | 20261126-170920 | 20261126-170920 | Tests are in seq 20 (tests/agent/test_http_lifecycle_health_check.py): 26 passed after the rewrite. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-170920 | 20261126-170920 | ruff format/check, mypy, lint-imports (6 contracts kept), bandit pass on this file; targeted tests 26 passed. Full suite pending at end of batch. Docs: N/A, docs update is seq 33's target row. startup_mcp_starter.py still pins is_degraded_but_live (2 mypy errors) until seq 05 lands. |

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
- **Requirement ID**: `REQ-001` (per-server timeout), `REQ-002` (deadline cap), `REQ-003` (single auth path), `REQ-005` (report-based readiness)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `scripts/agent/http_lifecycle_health_checker.py`