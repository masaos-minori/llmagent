## Goal

Remove the sentence in `mcp_02_02` that contradicts the fail-closed auth middleware and defer to ADR-017 instead (`REQ-005`, `AC-5`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Line 83 currently reads: "Empty server-side token (a standalone test run only): `attach_auth_middleware()` skips the authentication check and only injects `X-Request-Id`; the shell, github, file, and mdq servers refuse to start with an empty token."
- `attach_auth_middleware()` returns 401 for every request when the token is empty (fail-closed); there is no "standalone test run only" skip.

## Design decisions
- Replace the misleading last Bearer bullet with a single pointer sentence: every HTTP MCP server enforces the configured Bearer token, an empty token is fail-closed (401), and the full rule is defined by ADR-017.

## Alternatives considered
- Editing only part of the sentence: leaves the false "skips the authentication check" claim. Rejected: replace the whole bullet.

## Implementation
### Target file
`docs/22_mcp/mcp_02_02_startup-modes-and-health.md`

### Procedure
1. Replace the last Bearer bullet (line 83) with a pointer to ADR-017 consistent with the fail-closed middleware.

### Method
- New bullet: "Authentication is fail-closed: an empty server-side token makes `attach_auth_middleware()` reject every request with HTTP 401; the full rule (one shared variable per server on both sides, no bypass, restart required) is defined by [adr_02_03_017_mcp-authentication.md](../10_adr/adr_02_03_017_mcp-authentication.md)."

### Details
- Keep the preceding bullets (lines 80-82) that correctly describe the non-empty-token behavior.

### Companion test files
N/A.

## Compatibility considerations
- Cross-references `adr_02_03_017_mcp-authentication.md`; keep the relative path valid.

## Security considerations
- Removes a statement that understated the fail-closed guarantee.

## Rollback considerations
Revert the commit.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `mcp_02_02_startup-modes-and-health.md` | Doc claims vs code | `uv run python tools/check_docs_consistency.py --domain mcp` | Pass |

## Completion criteria
- No sentence in `mcp_02_02` contradicts ADR-017 or the fail-closed code; the rule defers to ADR-017.

## Out of Scope
- Other `mcp_02_02` content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace line 83 with an ADR-017 pointer | Pending | — | — | |
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
- **Requirement ID**: `REQ-005` — `mcp_02_02` no longer contradicts the fail-closed auth rule.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`
