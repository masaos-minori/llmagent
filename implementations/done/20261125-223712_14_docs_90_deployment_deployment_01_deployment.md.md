## Goal

Document the confinement posture a deployed host must satisfy, the development-only permissive opt-in, and that `GITHUB_TOKEN` now reaches only the servers that declare it (REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file already states the writable-directory rule at `:240`, the token-export notes at `:189-190`, and the token sections at `:200-232`; those are the places the new behavior touches.

## Design decisions

- Document the operator-visible contract (what aborts startup, which variable opts out), not the validator internals.
- Keep the strict default implicit: no variable is needed to get the safe mode.

## Alternatives considered

N/A: the content follows the Plan's Documentation Impact section.

## Implementation
### Target file
`docs/90_deployment/deployment_01_deployment.md`
### Procedure
Extend the compiled-artifacts bullet with the ownership and mode requirements, add the opt-in note, and restate the token-inheritance rule.

### Method
- `:240`: confinement is on by default; `/opt/llm/bin/` and every `mcp_<server>` binary must be owned by the user running the agent or by root and must not be group- or world-writable, and a binary failing these checks aborts startup with a `StartupFailure` naming the server and the path.
- After the export list at `:244-247`: `LLMAGENT_COMMAND_MODE` set to `permissive` restores the basename allowlist for development only; no deploy script sets it, and setting it in production disables the control described at `:240`.
- `:189-190`: `GITHUB_TOKEN` reaches a subprocess server only when that server's `[mcp_servers.*]` table declares `credential_env = ["GITHUB_TOKEN"]`, which is the case for `github` and `cicd`.
- Section 2.5 (`:200`): each server receives only its own `MCP_<SERVER_KEY_UPPER>_AUTH_TOKEN` and `MCP_<SERVER_KEY_UPPER>_CONTROL_TOKEN`.

## Compatibility considerations

N/A: the file is mirrored to `/opt/llm/docs/` by `deploy/deploy.sh`, so no extra step is needed.

## Security considerations

The permissive opt-in must not be presented as a supported production setting.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- the `tools/check_docs_*` gates in `rules/tool-gates.md` "When to run which tool"

## Completion criteria

- The file states the ownership and mode requirements, the strict-by-default posture, the opt-in with its production warning, and no statement implies a wildcard token pattern.

## Out of Scope

- `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` (row 13) and any `deploy/*.sh` change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document as described in Method | Completed | — | 20261126 | Execute after rows 1-3 and 6 land Document updated as specified. |
| 2 | Run the documentation gates in `rules/tool-gates.md` | Completed | — | 20261126 | check_docs_quality, check_docs_structure, check_docs_content_policy, check_docs_japanese, check_docs_consistency pass. |

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
- **Requirement ID**: REQ-010 (documentation of the confinement and credential-declaration contract)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `docs/90_deployment/deployment_01_deployment.md`