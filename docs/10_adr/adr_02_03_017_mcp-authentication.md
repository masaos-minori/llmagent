---
title: "ADR-017: MCP Bearer Authentication"
area: governance
tags:
  - mcp
  - authentication
  - security
related:
  - adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md
  - mcp_06_14_mcp-authentication-setup.md
  - mcp_02_02_startup-modes-and-health.md
---

# ADR-017: MCP Bearer Authentication

## Keywords

- mcp authentication
- bearer token
- auth_token
- fail-closed
- shared secret

## Status

Accepted

## Summary

ADR-017 is the single authoritative record of MCP Bearer authentication: one environment variable per MCP server resolved identically on the Agent side and the server side, an empty token aborts startup on both sides, the middleware is fail-closed with no bypass or accept-all mode, token changes take effect only on restart, and tokens are never logged. ADR-007 Decision 9 established that every MCP server carries Bearer authentication and deferred the details to a separate ADR; this ADR is that record. It documents rules already implemented in code; it does not introduce them.

## Context

### Problem

ADR-007 Decision 9 requires a non-empty authentication token and a matching Bearer header on every MCP server endpoint, and its Out of Scope defers "detailed implementation of security authentication" to a separate ADR that did not exist. The rules lived only in code and in scattered MCP documents, which had begun to describe superseded behavior (a test-only bypass since removed and an "empty token skips the check" reading of the middleware).

### Constraints

- Deployment is loopback-only (ADR-007): every MCP server binds to a loopback address and the supported caller is the single Agent process.
- The authentication layer decides whether a caller may use the MCP API; it is separate from mdq-mcp's `allowed_dirs` resource authorization, which applies only after successful authentication (ADR-007 Decision 9).
- The rules are already implemented; this ADR records them without changing behavior.

## Assumptions

- Single-operator, loopback deployment; re-evaluate if a server is ever exposed beyond localhost (see Review Triggers).
- Token values are supplied only through environment variables referenced from `config/agent.toml`; the repository never stores token values.

## Decision

### Decision Details

1. Each MCP server has exactly one dedicated environment variable, `MCP_<SERVER_KEY>_AUTH_TOKEN`, as its shared secret (for example `MCP_GIT_AUTH_TOKEN` for `git-mcp`).
2. The same variable is resolved on both sides: the Agent reads it through the `${ENV:MCP_<SERVER_KEY>_AUTH_TOKEN}` reference in `config/agent.toml`, and each server module reads the same variable for its own middleware configuration. One value, two resolution points, no separate server-side secret.
3. An empty token fails closed on both sides. Server side: `require_auth_token()` raises `RuntimeError` naming only the server label and the variable, and the server does not start. Agent side: `scripts/agent/startup_validation.py` records a fatal `mcp_auth` finding naming every enabled server whose `auth_token` is empty, and Agent startup stops. A disabled server is exempt from the Agent-side check.
4. The middleware is fail-closed: `attach_auth_middleware()` rejects every request with 401 when the configured token is empty, and no accept-all opt-out exists. The former test-only bypass was removed (commit `cad5e91ea`); no bypass mode is supported.
5. Token changes take effect only on restart: the token is read once at server startup and once at Agent config resolution, so rotation requires restarting the Agent and every affected MCP server.
6. Tokens are never logged or echoed: `require_auth_token()` names only the server and the variable, and no log line or audit record carries a token value.

### Scope

- **Components**: `scripts/mcp_servers/server.py` (`require_auth_token()`, `attach_auth_middleware()`), each MCP server module's startup path, `scripts/agent/startup_validation.py`, the `auth_token` entries of `config/agent.toml`.
- **Servers**: every configured HTTP MCP server (`shell`, `git`, `web_search`, `file_delete`, `file_write`, `file_read`, `github`, `cicd`, `rag_pipeline`, `mdq`).

### Out of Scope

- The HTTP transport choice itself (ADR-007).
- mdq-mcp's `allowed_dirs` path authorization (ADR-007 Decision 9; a separate boundary).
- Exposure beyond localhost and TLS (unsupported today; see ADR-007).
- The MCP audit-record content policy (governed by the MCP audit logging documents).

## Rationale

### 1. Single authoritative record

Authentication rules spread across code, MCP operation documents, and ADR-007's deferred pointer had begun to contradict each other. One ADR gives the rules a reviewable home that the MCP documents can reference instead of restating.

### 2. Fail-closed startup

A configured-but-unverified token is the worst authentication state: it looks configured and verifies nothing. Aborting both Agent and server startup on an empty token turns that silent state into an immediate, named startup failure.

### 3. One variable, both sides

Resolving the same environment variable on the Agent side and the server side removes the drift where a caller and a server are configured with different values and every call fails at the middleware instead of at startup.

## Alternatives Considered

### Alternative A: Extend ADR-007's decision text instead of a new ADR

- **Advantages:** No new ADR; fewer records to maintain.
- **Disadvantages:** ADR-007 already defers the authentication details to a separate ADR; folding the details into it reopens a large transport ADR and buries the security rules.
- **Reason for Rejection:** A dedicated ADR gives the rules a reviewable home, and ADR-007 keeps its role as the pointer (its Out of Scope line links to this ADR).

### Alternative B: Keep an empty-token accept-all mode for local development

- **Advantages:** Local test runs would not need a token.
- **Disadvantages:** An accept-all mode is exactly the configured-but-unverified state the fail-closed rule exists to prevent; the test-only bypass was already removed in commit `cad5e91ea`.
- **Reason for Rejection:** No bypass mode is supported; tests supply an explicit token instead.

## Consequences

### Positive Consequences
- Empty-token misconfiguration fails at startup with a named server and variable instead of failing per-request or silently skipping authentication.
- MCP documents gain one policy source to reference (INV-01..INV-05 below).

### Negative Consequences
- Token rotation requires restarting the Agent and every affected MCP server; there is no hot reload.
- Every new MCP server must route its token through `require_auth_token()`; a new server that bypasses it violates INV-03.

### Ongoing Risks
- New server modules or middleware call sites must keep routing through the shared enforcement point; the completeness tests in `tests/mcp_servers/test_require_auth_token.py` guard this.

### Operational Consequences
- Operators set one environment variable per server before starting the Agent; `mcp_06_14_mcp-authentication-setup.md` documents the setup.

### Security Consequences
- Unauthenticated requests are rejected with 401 on every endpoint, including when the token is empty (Explicit in code — `scripts/mcp_servers/server.py` `attach_auth_middleware()`, `require_auth_token()`).

## Invariants

- INV-01: An enabled MCP server configuration with an empty `auth_token` MUST produce a fatal `mcp_auth` finding at Agent startup.
- INV-02: Every configured server module MUST route its token through `require_auth_token()` and MUST refuse to start with an empty token.
- INV-03: `attach_auth_middleware()` with an empty token MUST return 401 for every request; no accept-all mode may be reintroduced.
- INV-04: A token value MUST NOT appear in log output or audit records; startup failure messages name only the server and the variable.
- INV-05: Each server's Agent-side `auth_token` and server-side token MUST resolve from the same `MCP_<SERVER_KEY>_AUTH_TOKEN` variable.

## Failure Policy

### Fail-Fast Conditions
- Empty `auth_token` for an enabled server: Agent startup records a fatal `mcp_auth` finding and stops; the server process raises `RuntimeError` at startup and does not bind.
- Missing or non-matching Bearer header: every request receives 401.

### Fail-Open or Degraded Conditions
- None for authentication. A disabled server skips the Agent-side `mcp_auth` check because its endpoint is not contacted.

### Retry Policy
Not applicable — a startup abort or a 401 is not retried automatically.

### Fallback Policy
Not applicable — there is no unauthenticated fallback path.

## Verification

### Automated Tests

| Test | Verifies | Type | Blocking |
|---|---|---|---|
| `tests/agent/test_startup_validation.py::TestMcpAuthDisabledServers::test_enabled_server_without_token_is_fatal_and_named` (and `test_disabled_server_without_token_passes_mcp_auth`) | INV-01 | Unit | Yes |
| `tests/mcp_servers/test_require_auth_token.py::TestRequireAuthToken::test_empty_token_raises`, `test_message_names_the_server_and_variable`, `test_non_empty_token_is_returned_unchanged`, `test_empty_token_prevents_every_server_from_importing` | INV-02, INV-04 | Unit | Yes |
| `tests/mcp_servers/test_require_auth_token.py::test_every_server_routes_through_shared_enforcement_point`, `test_attach_middleware_without_enforcement_point_is_flagged`, `test_every_configured_server_resolves_to_a_module_and_token_variable` | INV-02, INV-05 | Regression | Yes |
| `tests/mcp_servers/test_mcp_server_base.py::TestAttachAuthMiddleware::test_empty_token_denies_request_without_credentials`, `test_empty_token_accept_all_is_not_a_supported_mode`, `test_missing_token_returns_401`, `test_wrong_token_returns_401` | INV-03 | Unit | Yes |

## Implementation Notes

See Implementation References for the current file/symbol list.

## Known Deviations

Not applicable

## Review Triggers

- A server is exposed beyond the loopback address, or TLS is implemented (interacts with ADR-007).
- A caller other than the single Agent process is added, or a second environment variable for the same server becomes necessary.
- A token hot-reload or rotation-without-restart capability is proposed (Decision Details #5).

## Approval

### Required Reviewers
- Security Reviewer
- Documentation Governance Owner

### Approval Record

- **Approved By**: Task-level approval decision (repository owner; individual reviewer names are not recorded)
- **Approval Date**: 2026-11-12 (date the maintainer statement was given)
- **Approval Reference**: Reviewed and approved by the repository owner through a task-level approval decision issued 2026-11-12 as part of the MCP audit and authentication documentation task (`docs/00_governance/governance_01_documentation-policy.md` ADR Acceptance Evidence Standard)
- **Current Decision Approval**: Task-level approval decision (repository owner instruction) covers the current decision text; individual reviewer names are not recorded.

This ADR's `Accepted` status uses the task-level approval decision of 2026-11-12 defined by the governance document above as its acceptance evidence. No formal Approval Record with individual reviewer names was created.

## Related ADRs

- ADR-007: Adoption of HTTP MCP and Non-Support of stdio (Decision 9 requires Bearer authentication and defers its details to this ADR)

## Implementation References

- `scripts/mcp_servers/server.py` — `require_auth_token()`, `attach_auth_middleware()`
- `scripts/agent/startup_validation.py` — `mcp_auth` fatal finding for enabled servers with an empty `auth_token`
- `config/agent.toml` — `[mcp_servers.<key>].auth_token = "${ENV:MCP_<SERVER_KEY>_AUTH_TOKEN}"` entries
- Each server module's startup path (for example `scripts/mcp_servers/git/git_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`)
- Tests — `tests/mcp_servers/test_require_auth_token.py`, `tests/mcp_servers/test_mcp_server_base.py`, `tests/agent/test_startup_validation.py`

## Completion Checklist

Acceptance conditions and their current state.

- [x] The problem to solve is clear
- [x] The Decision is narrowed to one primary design decision
- [x] The Decision is stated in clear terms such as mandatory, prohibited, canonical, or Fallback conditions
- [x] The reasons for adoption are explained from perspectives other than the current implementation
- [x] Substantive alternatives and the reasons for rejecting them are recorded
- [x] Positive Consequences are recorded
- [x] Negative Consequences are recorded
- [x] The impact on Security has been evaluated
- [x] The impact on Operations, Monitoring, and Recovery has been evaluated
- [x] Verifiable Invariants are defined
- [x] Exceptions or out-of-scope cases are clear
