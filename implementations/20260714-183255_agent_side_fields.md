# Implementation Procedure: Consolidate MCP Configuration Ownership and Secret-Based Authentication Model (Agent-Side Fields)

## Goal

Restrict `agent.toml [mcp_servers.<key>]` field list to five confirmed fields only: `startup_mode`, `transport`, `url`, `healthcheck_mode`, `cmd`. Remove `auth_token`, `tool_names`, `env`, `role`, timeouts from field list.

## Scope

- `docs/04_mcp_06_mcpserverconfig-fields-agenttoml-mcp_servers.md` only
- Text removal and clarification; no new content creation beyond what's needed to replace obsolete descriptions

## Assumptions

1. The requirement `requires/20260714_08_require.md` is the canonical specification for this task.
2. The document currently lists more than five fields under `agent.toml [mcp_servers.<key>]`.
3. No source code changes are required — documentation updates only.

## Implementation

### Target file

`docs/04_mcp_06_mcpserverconfig-fields-agenttoml-mcp_servers.md`

### Procedure

1. **Scan for stale references**: Run grep across `docs/04_mcp_*` for patterns including raw `auth_token` references, stale split-config file names, `routing.md` references, and `tool_names` as routing input.
2. **Remove obsolete fields**: Delete `auth_token`, `tool_names`, `env`, `role`, timeouts from field list.
3. **Keep only five confirmed fields**: Retain `startup_mode`, `transport`, `url`, `healthcheck_mode`, `cmd`.

### Method

- Pattern-based search followed by targeted text deletion via file edit.

### Details

- Search for `auth_token`, `tool_names`, `env`, `role`, timeout patterns in the document
- Delete entire field entries for these obsolete fields
- Preserve surrounding context and formatting
- Ensure remaining five fields are clearly documented

## Validation plan

1. Verify only five confirmed fields remain in the field list.
2. Confirm no raw `auth_token` or other obsolete fields are mentioned.
3. Verify no broken cross-references from removed sections.
4. Run `pre-commit run --all-files` if linting is configured.
