## Goal

Document the per-server child environment, the new `credential_env` field, and the server-identifier rule in the MCP configuration reference (REQ-010).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Only the `env` section (`:21-44`) and the `key` paragraph (`:69`) describe the inherited environment and the derived key; both are edited in place.

## Design decisions

- Name `build_child_env` as the single builder: `filter_env` no longer exists after row 3.
- State the key rule as a pattern plus its rejection consequence, matching the Validation Rules section (`:73-75`).

## Alternatives considered

N/A: the content is fixed by REQ-010 and the Plan's Documentation Impact section.

## Implementation
### Target file
`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
### Procedure
Replace the inherited-variable list with the per-server model, add `credential_env`, and add the identifier rule to the `key` paragraph.

### Method
- `:21-28`: the child environment is built once per server by `build_child_env`, with the configured `env` merged on top; the fixed set is `PATH`, `HOME`, `USER`, `LOGNAME`, `SHELL`, `TMPDIR`, `TMP`, `TEMP`, `LANG`, `LC_*`, `LLMAGENT_CONFIG_DIR`, `LLMAGENT_SUDACHI_DICT`, and nothing else is inherited.
- `:29-38`: each server receives `MCP_<KEY>_AUTH_TOKEN` and `MCP_<KEY>_CONTROL_TOKEN` derived from its own section name, plus only the variables its own `credential_env` declares; another server's tokens and `GITHUB_TOKEN` are absent unless declared. Keep the tolerant control-token explanation.
- Add a `credential_env` paragraph: a list of variable names, not patterns, default empty, validated at parse time.
- `:69`: `key` must match `[a-z0-9][a-z0-9_-]{0,63}`, enforced by `validate_server_key` at `McpServerConfig`, `_build_mcp_servers`, and the stderr log directory.
- `:39-44`: keep "logged by key only, never by value" and restate the denylist and shell-server bullets for the per-server builder. Add `credential_env` to the Keywords list.

## Compatibility considerations

N/A: no other document states the inherited-variable list (Plan Design).

## Security considerations

The document is the operator-facing statement of which credential reaches which child; it must not imply a wildcard pattern still exists.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- the `tools/check_docs_*` gates in `rules/tool-gates.md` "When to run which tool"

## Completion criteria

- No remaining reference to `filter_env` or a wildcard token pattern; `credential_env` and the key pattern are documented with their enforcement points.

## Out of Scope

- `docs/90_deployment/deployment_01_deployment.md` (row 14) and the generated artifacts (rows 15-16).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the document as described in Method | Completed | — | 20261126 | Execute after rows 1-3 land Document updated as specified. |
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
- **Requirement ID**: REQ-010 (documentation of the per-server environment and the key rule)
- **Source issue**: issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-111909_cliplc006_mcp-launch-spec-credentials.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-223712
- **Related target files**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`