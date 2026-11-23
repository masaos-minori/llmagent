## Goal

Document the separate control authorization path and its fail-closed posture in the MCP access-control document.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: one new subsection and keyword entries. The Per-Server Access Control table is unchanged.

## Assumptions

- Verified: the document has a Per-Server Access Control table and sections for paths, repositories, and allowlists; no control-token text exists.

## Design decisions

- New section `## Control API Authorization` after `## Per-Server Access Control`.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`

### Procedure
1. State that control endpoints use a dedicated Bearer token from the server's own `[control]` table (`MCP_<NAME>_CONTROL_TOKEN`) and the Agent's `control_auth_token`, and that the tool token is rejected on control paths and the control token is rejected on tool paths.
2. State the fail-closed rules: an unset or empty control token closes only the control paths (401); tool authorization (ADR-017 INV-03 semantics) is unchanged; loopback binding is unchanged.
3. State that responses are structured evidence only and that a caller can read only the state of a logical call id it already holds.
4. Add keywords (control-token, call-state).

### Method
Prose only; cite `scripts/mcp_servers/control_api.py` and `scripts/mcp_servers/server.py` as the implementation sites.

### Details
- Do not change any ADR text or describe a maintainer approval.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The section describes the token separation, the fail-closed behavior, and the response restrictions; the documentation gates pass.

## Out of Scope

ADR documents and the endpoint response shape (row 31).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (separate control Bearer authorization), `REQ-007` (documentation of the control contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`
