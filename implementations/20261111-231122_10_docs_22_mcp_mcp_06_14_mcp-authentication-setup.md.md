## Goal

Correct the "Missing secrets via environment variables" troubleshooting entry in `mcp_06_14` that wrongly says "The server starts, but health checks fail", and defer the authentication rules to ADR-017 (`REQ-005`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 53 currently reads Symptom "The server starts, but health checks fail due to dependency failures."
- `require_auth_token()` raises `RuntimeError` for an empty token (`scripts/mcp_servers/server.py:134-144`), so a server with an empty `auth_token` does not start.

## Design decisions
- Correct the Symptom to reflect that an unset `auth_token` environment variable prevents the server from starting (fail-closed), and point the governing rules to ADR-017.

## Alternatives considered
- Leaving the "server starts" symptom: contradicts the fail-closed startup behavior. Rejected: correct it.

## Implementation
### Target file
`docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`

### Procedure
1. Fix the "Missing secrets via environment variables" Symptom (line 53): an unset `${ENV:...}` referenced by `auth_token` means the server does not start (empty token aborts startup).
2. Point the governing authentication rules to ADR-017 rather than restating them.

### Method
- New Symptom: "The MCP server fails to start because its `auth_token` resolves to an empty value."
- Keep the existing Cause/Solution wording aligned with the corrected symptom.

### Details
- Do not copy token values; reference ADR-017 for the full rule.

### Companion test files
N/A.

## Compatibility considerations
- Cross-references `adr_02_03_017_mcp-authentication.md`; keep the relative path valid.

## Security considerations
- Removes a statement that understated the fail-closed startup guarantee.

## Rollback considerations
Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `mcp_06_14_mcp-authentication-setup.md` | Doc claims vs code | `uv run python tools/check_docs_consistency.py --domain mcp` | Pass |

## Completion criteria
- The troubleshooting entry no longer claims the server starts with an empty `auth_token`; the rule defers to ADR-017.

## Out of Scope
- Other `mcp_06_14` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Correct the "Missing secrets" Symptom and defer to ADR-017 | Pending | — | — | |
| 2 | Run `check_docs_consistency.py --domain mcp` (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` — `mcp_06_14` no longer contradicts the fail-closed startup rule.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`
