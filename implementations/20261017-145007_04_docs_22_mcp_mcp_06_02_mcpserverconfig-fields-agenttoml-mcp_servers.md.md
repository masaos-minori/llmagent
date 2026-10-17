## Goal

Document the default-deny environment model for the MCP server `env` field, so an operator can see
which variables a subprocess server actually inherits and how to give it one that is not allowed.

## Scope

- `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md` (row 4 of the Plan's
  `Implementation Target Files`): replace the denylist-only sentence for `env` (lines 20-22) with
  the inheritance model, the allowed-variable list, and the server-`env` override route.

## Assumptions

- The chapter is the only doc that describes the `env` field's filtering (verified 2026-10-17:
  lines 20-22 are the only `LD_PRELOAD` mention in `docs/22_mcp/`).
- The chapter is 55 lines, well under the `check_docs_structure.py` size ceiling, so adding a short
  subsection does not need a size exception.

## Design decisions

- State the model in three sentences plus one list: inherited variables are only those matched by
  `_DEFAULT_ALLOWED_ENV_VARS`; the server's own `env` entries are merged after the denylist and
  protected-var filters; a variable outside the allowlist is declared in that server's `env`.
- Name the allowed variables explicitly (operators need the list to diagnose a server that cannot
  start), and name the excluded groups (credentials, proxy variables, interpreter toolchain
  variables) so the boundary is not guessed.

## Alternatives considered

N/A: documentation-only change confined to one paragraph; the Plan already fixed the wording scope.

## Implementation
### Target file
`docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
### Procedure
Replace lines 20-22 with the default-deny statement, the allowed-variable list, and the override
route; keep the surrounding field tables unchanged.
### Method
Single in-place edit of one paragraph.
### Details
- Keep the existing denylist sentence (it stays true) and add the inheritance sentence next to it
  rather than replacing it, so the `env` key-validation rules described elsewhere still match.
- Write in English per `skills/DESIGN.md` Output language.

## Compatibility considerations

N/A: documentation only; no runtime behavior changes in this file.

## Security considerations

Records the boundary that keeps unrelated parent credentials out of subprocess environments, and the
residual that the shared auth tokens are carried by a wildcard pattern.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
- `uv run python tools/check_docs_content_policy.py --strict`
- `uv run python tools/check_docs_consistency.py --domain mcp`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The chapter states the default-deny model, the allowed variables, and the server-`env` override
  route (`AC-008`).
- All five docs checkers above pass.

## Out of scope

- Any other `docs/` chapter, and `docs/90_deployment` (the compiled-binary environment case stays an
  assumption, Plan `UNK-05`).
- `config/agent.toml` and `config/*_mcp_server.toml` (Reference Files).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `env` denylist-only paragraph | Pending | — | — | |
| 2 | Run the docs checkers named in the Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`, `REQ-007`
- **Source issue**: `issues/20261016-093044_mcp004_filter_env_secret_logging_env_leak.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261016-110959_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261017-145007
- **Related target files**: `docs/22_mcp/mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md`
